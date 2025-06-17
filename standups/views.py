from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q, Count, Avg
from datetime import timedelta
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import Standup, StandupResponse, StandupReminder, StandupMetrics
from .serializers import (
    StandupSerializer, StandupResponseSerializer, StandupReminderSerializer,
    StandupMetricsSerializer, DashboardSerializer
)
from teams.models import TeamMember


@extend_schema_view(
    list=extend_schema(
        description="List all standups for the authenticated user's teams",
        summary="List standups",
        tags=["Standups"]
    ),
    create=extend_schema(
        description="Create a new standup for a team",
        summary="Create standup",
        tags=["Standups"]
    ),
    retrieve=extend_schema(
        description="Retrieve a specific standup",
        summary="Get standup",
        tags=["Standups"]
    ),
    update=extend_schema(
        description="Update a standup",
        summary="Update standup",
        tags=["Standups"]
    ),
    destroy=extend_schema(
        description="Delete a standup",
        summary="Delete standup",
        tags=["Standups"]
    ),
)
class StandupViewSet(viewsets.ModelViewSet):
    """API viewset for managing standups"""
    queryset = Standup.objects.all()
    serializer_class = StandupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter standups based on user's teams"""
        user = self.request.user
        if user.is_superuser:
            return Standup.objects.all()
        
        # Return standups for teams where user is a member
        return Standup.objects.filter(
            team__teammember__user=user,
            team__teammember__is_active=True
        ).distinct().order_by('-date')

    @extend_schema(
        description="Get all responses for a specific standup",
        summary="Get standup responses",
        responses=StandupResponseSerializer(many=True),
        tags=["Standups"]
    )
    @action(detail=True, methods=['get'])
    def responses(self, request, pk=None):
        """Get responses for a standup"""
        standup = self.get_object()
        responses = standup.responses.all().order_by('submitted_at')
        serializer = StandupResponseSerializer(responses, many=True)
        return Response(serializer.data)

    @extend_schema(
        description="Get team members who haven't submitted standup responses",
        summary="Get missing members",
        tags=["Standups"]
    )
    @action(detail=True, methods=['get'])
    def missing_members(self, request, pk=None):
        """Get team members who haven't submitted responses"""
        standup = self.get_object()
        missing = standup.missing_members
        
        missing_data = []
        for member in missing:
            missing_data.append({
                'id': member.id,
                'user': {
                    'id': member.user.id,
                    'username': member.user.username,
                    'full_name': member.user.get_full_name() or member.user.username
                },
                'role': member.role,
                'slack_user_id': member.slack_user_id
            })
        
        return Response(missing_data)

    @action(detail=True, methods=['post'])
    def end_standup(self, request, pk=None):
        """Manually end a standup"""
        standup = self.get_object()
        
        # Check permissions
        user_membership = TeamMember.objects.filter(
            team=standup.team,
            user=request.user,
            role__in=['lead', 'admin'],
            is_active=True
        ).first()
        
        if not user_membership and not request.user.is_superuser:
            return Response(
                {"error": "Permission denied"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if standup.status != 'in_progress':
            return Response(
                {"error": "Can only end standups that are in progress"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # End the standup
        standup.status = 'completed'
        standup.ended_at = timezone.now()
        standup.save()
        
        # Trigger summary generation
        from .tasks import end_standup
        end_standup.delay(standup.id)
        
        serializer = self.get_serializer(standup)
        return Response(serializer.data)


class StandupResponseViewSet(viewsets.ModelViewSet):
    """API viewset for managing standup responses"""
    queryset = StandupResponse.objects.all()
    serializer_class = StandupResponseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter responses based on user permissions"""
        user = self.request.user
        if user.is_superuser:
            return StandupResponse.objects.all()
        
        # Users can see responses from their teams
        return StandupResponse.objects.filter(
            Q(user=user) |  # Own responses
            Q(standup__team__teammember__user=user,
              standup__team__teammember__is_active=True)  # Team responses
        ).distinct().order_by('-submitted_at')

    def perform_create(self, serializer):
        """Set the user when creating a response"""
        serializer.save(user=self.request.user)


class StandupMetricsViewSet(viewsets.ReadOnlyModelViewSet):
    """API viewset for viewing standup metrics"""
    queryset = StandupMetrics.objects.all()
    serializer_class = StandupMetricsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter metrics based on user's teams"""
        user = self.request.user
        if user.is_superuser:
            return StandupMetrics.objects.all()
        
        return StandupMetrics.objects.filter(
            team__teammember__user=user,
            team__teammember__is_active=True
        ).distinct().order_by('-date')

    @action(detail=False, methods=['get'])
    def team_summary(self, request):
        """Get metrics summary for user's teams"""
        user = request.user
        
        # Get last 30 days of metrics for user's teams
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        
        metrics = self.get_queryset().filter(date__gte=thirty_days_ago)
        
        # Aggregate by team
        team_summaries = {}
        for metric in metrics:
            team_id = metric.team.id
            if team_id not in team_summaries:
                team_summaries[team_id] = {
                    'team': {
                        'id': metric.team.id,
                        'name': metric.team.name
                    },
                    'avg_completion_rate': 0,
                    'total_standups': 0,
                    'mood_trends': {}
                }
            
            summary = team_summaries[team_id]
            summary['total_standups'] += 1
            summary['avg_completion_rate'] += metric.completion_rate
            
            # Aggregate mood data
            for mood, count in metric.mood_distribution.items():
                if mood not in summary['mood_trends']:
                    summary['mood_trends'][mood] = 0
                summary['mood_trends'][mood] += count
        
        # Calculate averages
        for summary in team_summaries.values():
            if summary['total_standups'] > 0:
                summary['avg_completion_rate'] /= summary['total_standups']
        
        return Response(list(team_summaries.values()))


class DashboardView(APIView):
    """Dashboard view with user and team statistics"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.now().date()
        last_week = today - timedelta(days=7)
        
        # User statistics
        user_teams = TeamMember.objects.filter(user=user, is_active=True)
        user_responses = StandupResponse.objects.filter(
            user=user,
            submitted_at__date__gte=last_week
        )
        
        user_stats = {
            'teams_count': user_teams.count(),
            'responses_this_week': user_responses.count(),
            'current_streak': self._calculate_streak(user),
            'avg_mood_this_week': self._calculate_avg_mood(user_responses)
        }
        
        # Team statistics
        team_stats = []
        for membership in user_teams:
            team = membership.team
            recent_standups = Standup.objects.filter(
                team=team,
                date__gte=last_week
            )
            
            if recent_standups.exists():
                avg_completion = sum(s.completion_rate for s in recent_standups) / len(recent_standups)
                team_stats.append({
                    'team': {
                        'id': team.id,
                        'name': team.name
                    },
                    'standups_this_week': recent_standups.count(),
                    'avg_completion_rate': avg_completion,
                    'user_participation': recent_standups.filter(
                        responses__user=user
                    ).count()
                })
        
        # Recent standups
        recent_standups = Standup.objects.filter(
            team__teammember__user=user,
            team__teammember__is_active=True
        ).distinct().order_by('-date')[:5]
        
        # Recent responses
        recent_responses = StandupResponse.objects.filter(
            standup__team__teammember__user=user,
            standup__team__teammember__is_active=True
        ).distinct().order_by('-submitted_at')[:10]
        
        data = {
            'user_stats': user_stats,
            'team_stats': team_stats,
            'recent_standups': StandupSerializer(recent_standups, many=True).data,
            'recent_responses': StandupResponseSerializer(recent_responses, many=True).data
        }
        
        return Response(data)
    
    def _calculate_streak(self, user):
        """Calculate user's current standup streak"""
        # This is a simplified version - you might want to implement more sophisticated logic
        responses = StandupResponse.objects.filter(user=user).order_by('-submitted_at')
        
        if not responses.exists():
            return 0
        
        streak = 0
        current_date = timezone.now().date()
        
        for response in responses:
            response_date = response.submitted_at.date()
            if response_date == current_date or response_date == current_date - timedelta(days=1):
                streak += 1
                current_date = response_date - timedelta(days=1)
            else:
                break
        
        return streak
    
    def _calculate_avg_mood(self, responses):
        """Calculate average mood score"""
        if not responses.exists():
            return 0
        
        mood_scores = {
            'great': 5,
            'good': 4,
            'okay': 3,
            'stressed': 2,
            'blocked': 1
        }
        
        total_score = sum(mood_scores.get(r.mood, 3) for r in responses)
        return total_score / responses.count()
