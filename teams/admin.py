from django.contrib import admin
from .models import Team, TeamMember, StandupSchedule


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'slack_channel_id', 'is_active', 'member_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'slack_channel_id']
    readonly_fields = ['created_at', 'updated_at']
    
    def member_count(self, obj):
        return obj.teammember_set.filter(is_active=True).count()
    member_count.short_description = 'Active Members'


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ['user', 'team', 'role', 'is_active', 'joined_at']
    list_filter = ['role', 'is_active', 'team', 'joined_at']
    search_fields = ['user__username', 'user__email', 'team__name', 'slack_user_id']
    readonly_fields = ['joined_at']


@admin.register(StandupSchedule)
class StandupScheduleAdmin(admin.ModelAdmin):
    list_display = ['team', 'reminder_time', 'end_time', 'timezone', 'is_active', 'weekdays_display']
    list_filter = ['is_active', 'timezone', 'team']
    search_fields = ['team__name']
    readonly_fields = ['created_at']
    
    def weekdays_display(self, obj):
        weekday_map = {
            1: 'Mon', 2: 'Tue', 3: 'Wed', 4: 'Thu',
            5: 'Fri', 6: 'Sat', 7: 'Sun'
        }
        return ', '.join([weekday_map.get(day, '') for day in obj.weekdays])
    weekdays_display.short_description = 'Weekdays'
