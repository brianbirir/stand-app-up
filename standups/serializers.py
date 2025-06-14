from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Standup, StandupResponse, StandupReminder, StandupMetrics
from teams.serializers import UserSerializer, TeamSerializer


class StandupSerializer(serializers.ModelSerializer):
    """Serializer for Standup model"""
    team = TeamSerializer(read_only=True)
    completion_rate = serializers.ReadOnlyField()
    response_count = serializers.SerializerMethodField()
    missing_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Standup
        fields = ['id', 'team', 'date', 'status', 'started_at', 'ended_at',
                 'completion_rate', 'response_count', 'missing_count', 'created_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_response_count(self, obj):
        return obj.responses.count()
    
    def get_missing_count(self, obj):
        return obj.missing_members.count()


class StandupResponseSerializer(serializers.ModelSerializer):
    """Serializer for StandupResponse model"""
    user = UserSerializer(read_only=True)
    standup_info = serializers.SerializerMethodField()
    
    class Meta:
        model = StandupResponse
        fields = ['id', 'user', 'standup', 'standup_info', 'yesterday_work', 
                 'today_work', 'blockers', 'mood', 'submitted_at', 'updated_at']
        read_only_fields = ['submitted_at', 'updated_at']
    
    def get_standup_info(self, obj):
        return {
            'team_name': obj.standup.team.name,
            'date': obj.standup.date,
            'status': obj.standup.status
        }


class StandupReminderSerializer(serializers.ModelSerializer):
    """Serializer for StandupReminder model"""
    user = UserSerializer(read_only=True)
    standup_info = serializers.SerializerMethodField()
    
    class Meta:
        model = StandupReminder
        fields = ['id', 'user', 'standup', 'standup_info', 'reminder_type', 
                 'sent_at', 'responded']
        read_only_fields = ['sent_at']
    
    def get_standup_info(self, obj):
        return {
            'team_name': obj.standup.team.name,
            'date': obj.standup.date
        }


class StandupMetricsSerializer(serializers.ModelSerializer):
    """Serializer for StandupMetrics model"""
    team = TeamSerializer(read_only=True)
    
    class Meta:
        model = StandupMetrics
        fields = ['id', 'team', 'date', 'total_members', 'responses_count',
                 'completion_rate', 'average_response_time', 'first_response_time',
                 'last_response_time', 'mood_distribution', 'created_at']
        read_only_fields = ['created_at']


class DashboardSerializer(serializers.Serializer):
    """Serializer for dashboard data"""
    user_stats = serializers.DictField()
    team_stats = serializers.ListField()
    recent_standups = StandupSerializer(many=True)
    recent_responses = StandupResponseSerializer(many=True)