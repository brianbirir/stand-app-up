from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator


class Team(models.Model):
    """Model representing a team that participates in stand-ups"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    slack_channel_id = models.CharField(
        max_length=50, 
        unique=True,
        validators=[RegexValidator(
            regex=r'^C[A-Z0-9]{8,}$',
            message='Invalid Slack channel ID format'
        )]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class TeamMember(models.Model):
    """Model representing a user's membership in a team"""
    ROLE_CHOICES = [
        ('member', 'Member'),
        ('lead', 'Team Lead'),
        ('admin', 'Admin'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    slack_user_id = models.CharField(
        max_length=50,
        validators=[RegexValidator(
            regex=r'^U[A-Z0-9]{8,}$',
            message='Invalid Slack user ID format'
        )]
    )
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'team']
        ordering = ['team__name', 'user__username']

    def __str__(self):
        return f"{self.user.username} - {self.team.name} ({self.role})"


class StandupSchedule(models.Model):
    """Model for configuring stand-up schedules for teams"""
    WEEKDAY_CHOICES = [
        (1, 'Monday'),
        (2, 'Tuesday'), 
        (3, 'Wednesday'),
        (4, 'Thursday'),
        (5, 'Friday'),
        (6, 'Saturday'),
        (7, 'Sunday'),
    ]

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='schedules')
    weekdays = models.JSONField(default=list)  # List of weekday numbers
    reminder_time = models.TimeField()  # When to send reminder
    end_time = models.TimeField()  # When to end stand-up collection
    timezone = models.CharField(max_length=50, default='UTC')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.team.name} - {self.reminder_time}"

    class Meta:
        ordering = ['team__name', 'reminder_time']
