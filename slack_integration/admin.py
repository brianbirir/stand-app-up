from django.contrib import admin
from .models import SlackWorkspace, SlackMessage, SlackInteraction, SlackUserMapping, SlackChannelMapping


@admin.register(SlackWorkspace)
class SlackWorkspaceAdmin(admin.ModelAdmin):
    list_display = ['team_name', 'team_id', 'bot_user_id', 'is_active', 'installed_at']
    list_filter = ['is_active', 'installed_at']
    search_fields = ['team_name', 'team_id', 'bot_user_id']
    readonly_fields = ['installed_at', 'updated_at']


@admin.register(SlackMessage)
class SlackMessageAdmin(admin.ModelAdmin):
    list_display = ['workspace', 'channel_id', 'message_type', 'sent_at']
    list_filter = ['message_type', 'sent_at', 'workspace']
    search_fields = ['channel_id', 'user_id', 'content']
    readonly_fields = ['sent_at']
    date_hierarchy = 'sent_at'


@admin.register(SlackInteraction)
class SlackInteractionAdmin(admin.ModelAdmin):
    list_display = ['workspace', 'user_id', 'interaction_type', 'created_at']
    list_filter = ['interaction_type', 'created_at', 'workspace']
    search_fields = ['user_id', 'callback_id', 'trigger_id']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'


@admin.register(SlackUserMapping)
class SlackUserMappingAdmin(admin.ModelAdmin):
    list_display = ['user', 'slack_username', 'workspace', 'is_active', 'created_at']
    list_filter = ['is_active', 'workspace', 'created_at']
    search_fields = ['user__username', 'slack_username', 'slack_user_id', 'slack_email']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(SlackChannelMapping)
class SlackChannelMappingAdmin(admin.ModelAdmin):
    list_display = ['team', 'channel_name', 'workspace', 'is_private', 'is_active']
    list_filter = ['is_private', 'is_active', 'workspace']
    search_fields = ['team__name', 'channel_name', 'channel_id']
    readonly_fields = ['created_at', 'updated_at']
