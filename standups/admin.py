from django.contrib import admin
from .models import Standup, StandupResponse, StandupReminder, StandupMetrics


@admin.register(Standup)
class StandupAdmin(admin.ModelAdmin):
    list_display = ['team', 'date', 'status', 'completion_rate_display', 'started_at', 'ended_at']
    list_filter = ['status', 'date', 'team', 'created_at']
    search_fields = ['team__name']
    readonly_fields = ['created_at', 'updated_at', 'completion_rate_display']
    date_hierarchy = 'date'
    
    def completion_rate_display(self, obj):
        return f"{obj.completion_rate:.1f}%"
    completion_rate_display.short_description = 'Completion Rate'


@admin.register(StandupResponse)
class StandupResponseAdmin(admin.ModelAdmin):
    list_display = ['user', 'standup', 'mood', 'submitted_at']
    list_filter = ['mood', 'submitted_at', 'standup__team']
    search_fields = ['user__username', 'standup__team__name', 'yesterday_work', 'today_work']
    readonly_fields = ['submitted_at', 'updated_at']
    date_hierarchy = 'submitted_at'


@admin.register(StandupReminder)
class StandupReminderAdmin(admin.ModelAdmin):
    list_display = ['user', 'standup', 'reminder_type', 'sent_at', 'responded']
    list_filter = ['reminder_type', 'responded', 'sent_at', 'standup__team']
    search_fields = ['user__username', 'standup__team__name']
    readonly_fields = ['sent_at']
    date_hierarchy = 'sent_at'


@admin.register(StandupMetrics)
class StandupMetricsAdmin(admin.ModelAdmin):
    list_display = ['team', 'date', 'completion_rate', 'responses_count', 'total_members']
    list_filter = ['date', 'team']
    search_fields = ['team__name']
    readonly_fields = ['created_at']
    date_hierarchy = 'date'
