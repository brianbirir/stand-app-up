from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Team, TeamMember, StandupSchedule


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class TeamSerializer(serializers.ModelSerializer):
    """Serializer for Team model"""
    member_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Team
        fields = ['id', 'name', 'description', 'slack_channel_id', 'is_active', 
                 'created_at', 'updated_at', 'member_count']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_member_count(self, obj):
        return obj.teammember_set.filter(is_active=True).count()


class TeamMemberSerializer(serializers.ModelSerializer):
    """Serializer for TeamMember model"""
    user = UserSerializer(read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)
    
    class Meta:
        model = TeamMember
        fields = ['id', 'user', 'team', 'team_name', 'role', 'slack_user_id', 
                 'is_active', 'joined_at']
        read_only_fields = ['joined_at']


class StandupScheduleSerializer(serializers.ModelSerializer):
    """Serializer for StandupSchedule model"""
    team_name = serializers.CharField(source='team.name', read_only=True)
    weekday_names = serializers.SerializerMethodField()
    
    class Meta:
        model = StandupSchedule
        fields = ['id', 'team', 'team_name', 'weekdays', 'weekday_names', 
                 'reminder_time', 'end_time', 'timezone', 'is_active', 'created_at']
        read_only_fields = ['created_at']
    
    def get_weekday_names(self, obj):
        weekday_map = {
            1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday',
            5: 'Friday', 6: 'Saturday', 7: 'Sunday'
        }
        return [weekday_map.get(day, '') for day in obj.weekdays]