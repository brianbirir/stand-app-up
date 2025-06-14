from django.db import models
from django.contrib.auth.models import User
from teams.models import Team
from standups.models import Standup


class SlackWorkspace(models.Model):
    """Model representing a connected Slack workspace"""
    team_id = models.CharField(max_length=50, unique=True)
    team_name = models.CharField(max_length=100)
    bot_user_id = models.CharField(max_length=50)
    bot_access_token = models.TextField()
    is_active = models.BooleanField(default=True)
    installed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.team_name} ({self.team_id})"

    class Meta:
        ordering = ['team_name']


class SlackMessage(models.Model):
    """Model for tracking Slack messages sent by the bot"""
    MESSAGE_TYPES = [
        ('reminder', 'Stand-up Reminder'),
        ('summary', 'Stand-up Summary'),
        ('follow_up', 'Follow-up Reminder'),
        ('response', 'Stand-up Response'),
        ('notification', 'Notification'),
    ]

    workspace = models.ForeignKey(SlackWorkspace, on_delete=models.CASCADE)
    channel_id = models.CharField(max_length=50)
    user_id = models.CharField(max_length=50, null=True, blank=True)
    message_ts = models.CharField(max_length=50, unique=True)
    thread_ts = models.CharField(max_length=50, null=True, blank=True)
    message_type = models.CharField(max_length=15, choices=MESSAGE_TYPES)
    content = models.TextField()
    standup = models.ForeignKey(Standup, on_delete=models.CASCADE, null=True, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.message_type} - {self.channel_id} - {self.sent_at}"

    class Meta:
        ordering = ['-sent_at']


class SlackInteraction(models.Model):
    """Model for tracking Slack interactions (button clicks, modal submissions, etc.)"""
    INTERACTION_TYPES = [
        ('button_click', 'Button Click'),
        ('modal_submission', 'Modal Submission'),
        ('slash_command', 'Slash Command'),
        ('message_action', 'Message Action'),
    ]

    workspace = models.ForeignKey(SlackWorkspace, on_delete=models.CASCADE)
    user_id = models.CharField(max_length=50)
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    trigger_id = models.CharField(max_length=100, null=True, blank=True)
    callback_id = models.CharField(max_length=100, null=True, blank=True)
    payload = models.JSONField()
    response_data = models.JSONField(null=True, blank=True)
    standup = models.ForeignKey(Standup, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.interaction_type} - {self.user_id} - {self.created_at}"

    class Meta:
        ordering = ['-created_at']


class SlackUserMapping(models.Model):
    """Model for mapping Django users to Slack users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    slack_user_id = models.CharField(max_length=50, unique=True)
    slack_username = models.CharField(max_length=100)
    slack_email = models.EmailField(null=True, blank=True)
    workspace = models.ForeignKey(SlackWorkspace, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} -> {self.slack_username}"

    class Meta:
        unique_together = ['slack_user_id', 'workspace']
        ordering = ['user__username']


class SlackChannelMapping(models.Model):
    """Model for mapping Teams to Slack channels"""
    team = models.OneToOneField(Team, on_delete=models.CASCADE)
    workspace = models.ForeignKey(SlackWorkspace, on_delete=models.CASCADE)
    channel_id = models.CharField(max_length=50)
    channel_name = models.CharField(max_length=100)
    is_private = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.team.name} -> #{self.channel_name}"

    class Meta:
        unique_together = ['channel_id', 'workspace']
        ordering = ['team__name']
