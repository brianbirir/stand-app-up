from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Team, TeamMember, StandupSchedule
from .serializers import TeamSerializer, TeamMemberSerializer, StandupScheduleSerializer


class TeamViewSet(viewsets.ModelViewSet):
    """API viewset for managing teams"""
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter teams based on user permissions"""
        user = self.request.user
        if user.is_superuser:
            return Team.objects.all()
        
        # Return teams where user is a member
        return Team.objects.filter(
            teammember__user=user,
            teammember__is_active=True
        ).distinct()

    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """Get team members"""
        team = self.get_object()
        members = TeamMember.objects.filter(team=team, is_active=True)
        serializer = TeamMemberSerializer(members, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """Add a member to the team"""
        team = self.get_object()
        
        # Check if user has permission to add members
        user_membership = TeamMember.objects.filter(
            team=team,
            user=request.user,
            role__in=['lead', 'admin'],
            is_active=True
        ).first()
        
        if not user_membership and not request.user.is_superuser:
            return Response(
                {"error": "Permission denied"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        username = request.data.get('username')
        slack_user_id = request.data.get('slack_user_id')
        role = request.data.get('role', 'member')
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user is already a member
        if TeamMember.objects.filter(team=team, user=user).exists():
            return Response(
                {"error": "User is already a member of this team"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        member = TeamMember.objects.create(
            team=team,
            user=user,
            role=role,
            slack_user_id=slack_user_id
        )
        
        serializer = TeamMemberSerializer(member)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TeamMemberViewSet(viewsets.ModelViewSet):
    """API viewset for managing team members"""
    queryset = TeamMember.objects.all()
    serializer_class = TeamMemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter based on user permissions"""
        user = self.request.user
        if user.is_superuser:
            return TeamMember.objects.all()
        
        # Return memberships for teams where user is a member
        return TeamMember.objects.filter(
            team__teammember__user=user,
            team__teammember__is_active=True
        ).distinct()


class StandupScheduleViewSet(viewsets.ModelViewSet):
    """API viewset for managing standup schedules"""
    queryset = StandupSchedule.objects.all()
    serializer_class = StandupScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter based on user permissions"""
        user = self.request.user
        if user.is_superuser:
            return StandupSchedule.objects.all()
        
        # Return schedules for teams where user is a lead or admin
        return StandupSchedule.objects.filter(
            team__teammember__user=user,
            team__teammember__role__in=['lead', 'admin'],
            team__teammember__is_active=True
        ).distinct()
