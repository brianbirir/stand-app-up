from django.db import models
from django.contrib.auth.models import User
from teams.models import Team


class Standup(models.Model):
    """Model representing a daily stand-up session"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='standups')
    date = models.DateField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    slack_thread_ts = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['team', 'date']
        ordering = ['-date', 'team__name']

    def __str__(self):
        return f"{self.team.name} - {self.date}"

    @property
    def completion_rate(self):
        """Calculate the percentage of team members who submitted stand-ups"""
        total_members = self.team.teammember_set.filter(is_active=True).count()
        submitted_count = self.responses.count()
        return (submitted_count / total_members * 100) if total_members > 0 else 0

    @property
    def missing_members(self):
        """Get list of team members who haven't submitted stand-ups"""
        submitted_user_ids = self.responses.values_list('user_id', flat=True)
        return self.team.teammember_set.filter(
            is_active=True
        ).exclude(user_id__in=submitted_user_ids)


class StandupResponse(models.Model):
    """Model representing an individual's stand-up response"""
    standup = models.ForeignKey(Standup, on_delete=models.CASCADE, related_name='responses')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # The three standard stand-up questions
    yesterday_work = models.TextField(help_text="What did you work on yesterday?")
    today_work = models.TextField(help_text="What will you work on today?")
    blockers = models.TextField(blank=True, help_text="Are there any blockers or impediments?")
    
    # Additional fields
    mood = models.CharField(
        max_length=20,
        choices=[
            ('great', '😄 Great'),
            ('good', '😊 Good'),
            ('okay', '😐 Okay'),
            ('stressed', '😰 Stressed'),
            ('blocked', '😤 Blocked'),
        ],
        default='good'
    )
    
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    slack_message_ts = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        unique_together = ['standup', 'user']
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.user.username} - {self.standup.date}"


class StandupReminder(models.Model):
    """Model for tracking stand-up reminders sent to users"""
    REMINDER_TYPES = [
        ('initial', 'Initial Reminder'),
        ('follow_up', 'Follow-up Reminder'),
        ('final', 'Final Reminder'),
    ]

    standup = models.ForeignKey(Standup, on_delete=models.CASCADE, related_name='reminders')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reminder_type = models.CharField(max_length=15, choices=REMINDER_TYPES)
    sent_at = models.DateTimeField(auto_now_add=True)
    slack_message_ts = models.CharField(max_length=50, null=True, blank=True)
    responded = models.BooleanField(default=False)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"{self.reminder_type} - {self.user.username} - {self.standup.date}"


class StandupMetrics(models.Model):
    """Model for storing stand-up metrics and analytics"""
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='metrics')
    date = models.DateField()
    
    # Participation metrics
    total_members = models.IntegerField()
    responses_count = models.IntegerField()
    completion_rate = models.FloatField()
    
    # Timing metrics
    average_response_time = models.DurationField(null=True, blank=True)
    first_response_time = models.TimeField(null=True, blank=True)
    last_response_time = models.TimeField(null=True, blank=True)
    
    # Mood metrics
    mood_distribution = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['team', 'date']
        ordering = ['-date', 'team__name']

    def __str__(self):
        return f"{self.team.name} metrics - {self.date}"
