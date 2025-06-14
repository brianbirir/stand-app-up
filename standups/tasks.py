from celery import shared_task
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import datetime, time, timedelta
import pytz

from teams.models import Team, TeamMember, StandupSchedule
from standups.models import Standup, StandupResponse, StandupReminder, StandupMetrics
from slack_integration.services import SlackService


@shared_task
def send_standup_reminders():
    """Send initial stand-up reminders based on team schedules"""
    now = timezone.now()
    current_weekday = now.weekday() + 1  # Django uses 1-7 for Monday-Sunday
    
    # Get all active schedules for today
    schedules = StandupSchedule.objects.filter(
        is_active=True,
        weekdays__contains=current_weekday,
        team__is_active=True
    )
    
    for schedule in schedules:
        # Convert schedule time to UTC
        team_tz = pytz.timezone(schedule.timezone)
        schedule_time = team_tz.localize(
            datetime.combine(now.date(), schedule.reminder_time)
        ).astimezone(pytz.UTC)
        
        # Check if it's time to send reminder (within 1 minute window)
        if abs((now - schedule_time).total_seconds()) <= 60:
            create_and_send_standup_reminder.delay(schedule.team.id)


@shared_task
def create_and_send_standup_reminder(team_id):
    """Create stand-up session and send reminders to team members"""
    try:
        team = Team.objects.get(id=team_id, is_active=True)
        today = timezone.now().date()
        
        # Get or create today's stand-up
        standup, created = Standup.objects.get_or_create(
            team=team,
            date=today,
            defaults={'status': 'in_progress', 'started_at': timezone.now()}
        )
        
        if not created and standup.status == 'completed':
            return f"Stand-up for {team.name} already completed"
        
        # Update status if it was pending
        if standup.status == 'pending':
            standup.status = 'in_progress'
            standup.started_at = timezone.now()
            standup.save()
        
        # Get active team members
        active_members = TeamMember.objects.filter(
            team=team,
            is_active=True,
            user__is_active=True
        )
        
        slack_service = SlackService()
        
        for member in active_members:
            # Check if user already submitted stand-up
            if not StandupResponse.objects.filter(standup=standup, user=member.user).exists():
                # Send reminder
                reminder = StandupReminder.objects.create(
                    standup=standup,
                    user=member.user,
                    reminder_type='initial'
                )
                
                # Send Slack message
                message_ts = slack_service.send_standup_reminder(
                    member.slack_user_id,
                    standup,
                    reminder.reminder_type
                )
                
                if message_ts:
                    reminder.slack_message_ts = message_ts
                    reminder.save()
        
        return f"Sent reminders for {team.name} stand-up"
        
    except Team.DoesNotExist:
        return f"Team {team_id} not found"
    except Exception as e:
        return f"Error sending reminders: {str(e)}"


@shared_task
def send_follow_up_reminders():
    """Send follow-up reminders to users who haven't submitted stand-ups"""
    now = timezone.now()
    cutoff_time = now - timedelta(minutes=30)  # Send follow-up after 30 minutes
    
    # Get active stand-ups from today
    active_standups = Standup.objects.filter(
        date=now.date(),
        status='in_progress',
        started_at__lte=cutoff_time
    )
    
    slack_service = SlackService()
    
    for standup in active_standups:
        # Get missing members
        missing_members = standup.missing_members
        
        for member in missing_members:
            # Check if we've already sent a follow-up reminder
            last_reminder = StandupReminder.objects.filter(
                standup=standup,
                user=member.user,
                reminder_type='follow_up'
            ).first()
            
            if not last_reminder or (now - last_reminder.sent_at).total_seconds() > 3600:  # 1 hour
                reminder = StandupReminder.objects.create(
                    standup=standup,
                    user=member.user,
                    reminder_type='follow_up'
                )
                
                message_ts = slack_service.send_standup_reminder(
                    member.slack_user_id,
                    standup,
                    reminder.reminder_type
                )
                
                if message_ts:
                    reminder.slack_message_ts = message_ts
                    reminder.save()


@shared_task
def end_standups():
    """End stand-ups based on team schedules and send summaries"""
    now = timezone.now()
    
    # Get active stand-ups from today
    active_standups = Standup.objects.filter(
        date=now.date(),
        status='in_progress'
    )
    
    for standup in active_standups:
        # Get team's schedule for today
        current_weekday = now.weekday() + 1
        schedule = StandupSchedule.objects.filter(
            team=standup.team,
            is_active=True,
            weekdays__contains=current_weekday
        ).first()
        
        if schedule:
            # Convert end time to UTC
            team_tz = pytz.timezone(schedule.timezone)
            end_time = team_tz.localize(
                datetime.combine(now.date(), schedule.end_time)
            ).astimezone(pytz.UTC)
            
            # Check if it's time to end (within 5 minute window)
            if now >= end_time:
                end_standup.delay(standup.id)


@shared_task
def end_standup(standup_id):
    """End a specific stand-up and send summary"""
    try:
        standup = Standup.objects.get(id=standup_id)
        
        if standup.status != 'in_progress':
            return f"Stand-up {standup_id} not in progress"
        
        # Update standup status
        standup.status = 'completed'
        standup.ended_at = timezone.now()
        standup.save()
        
        # Generate metrics
        generate_standup_metrics.delay(standup.id)
        
        # Send summary to team channel
        slack_service = SlackService()
        slack_service.send_standup_summary(standup)
        
        return f"Ended stand-up for {standup.team.name} on {standup.date}"
        
    except Standup.DoesNotExist:
        return f"Stand-up {standup_id} not found"
    except Exception as e:
        return f"Error ending stand-up: {str(e)}"


@shared_task
def generate_standup_metrics(standup_id):
    """Generate metrics for a completed stand-up"""
    try:
        standup = Standup.objects.get(id=standup_id)
        
        # Calculate metrics
        total_members = standup.team.teammember_set.filter(is_active=True).count()
        responses = standup.responses.all()
        responses_count = responses.count()
        completion_rate = (responses_count / total_members * 100) if total_members > 0 else 0
        
        # Calculate timing metrics
        if responses.exists():
            response_times = [r.submitted_at for r in responses]
            first_response_time = min(response_times).time()
            last_response_time = max(response_times).time()
            
            # Calculate average response time from standup start
            if standup.started_at:
                total_duration = sum([
                    (r.submitted_at - standup.started_at).total_seconds() 
                    for r in responses
                ], 0)
                average_response_time = timedelta(seconds=total_duration / responses_count)
            else:
                average_response_time = None
        else:
            first_response_time = None
            last_response_time = None
            average_response_time = None
        
        # Calculate mood distribution
        mood_distribution = {}
        for response in responses:
            mood = response.mood
            mood_distribution[mood] = mood_distribution.get(mood, 0) + 1
        
        # Create or update metrics
        metrics, created = StandupMetrics.objects.update_or_create(
            team=standup.team,
            date=standup.date,
            defaults={
                'total_members': total_members,
                'responses_count': responses_count,
                'completion_rate': completion_rate,
                'average_response_time': average_response_time,
                'first_response_time': first_response_time,
                'last_response_time': last_response_time,
                'mood_distribution': mood_distribution,
            }
        )
        
        return f"Generated metrics for {standup.team.name} on {standup.date}"
        
    except Standup.DoesNotExist:
        return f"Stand-up {standup_id} not found"
    except Exception as e:
        return f"Error generating metrics: {str(e)}"


@shared_task
def generate_daily_metrics():
    """Generate daily metrics for all teams"""
    yesterday = (timezone.now() - timedelta(days=1)).date()
    
    completed_standups = Standup.objects.filter(
        date=yesterday,
        status='completed'
    )
    
    for standup in completed_standups:
        # Check if metrics already exist
        if not StandupMetrics.objects.filter(team=standup.team, date=standup.date).exists():
            generate_standup_metrics.delay(standup.id)


@shared_task
def process_standup_response(user_id, standup_id, response_data):
    """Process a stand-up response submission"""
    try:
        user = User.objects.get(id=user_id)
        standup = Standup.objects.get(id=standup_id)
        
        # Create or update response
        response, created = StandupResponse.objects.update_or_create(
            standup=standup,
            user=user,
            defaults={
                'yesterday_work': response_data.get('yesterday_work', ''),
                'today_work': response_data.get('today_work', ''),
                'blockers': response_data.get('blockers', ''),
                'mood': response_data.get('mood', 'good'),
                'slack_message_ts': response_data.get('message_ts'),
            }
        )
        
        # Mark any reminders as responded
        StandupReminder.objects.filter(
            standup=standup,
            user=user,
            responded=False
        ).update(responded=True)
        
        # Send confirmation message
        slack_service = SlackService()
        slack_service.send_response_confirmation(user, standup, response)
        
        return f"Processed stand-up response for {user.username}"
        
    except (User.DoesNotExist, Standup.DoesNotExist) as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Error processing response: {str(e)}"