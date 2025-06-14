import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'standapp.settings')

app = Celery('standapp')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery beat schedule for automated tasks
app.conf.beat_schedule = {
    'send-standup-reminders': {
        'task': 'standups.tasks.send_standup_reminders',
        'schedule': 60.0,  # Run every minute to check for scheduled reminders
    },
    'send-follow-up-reminders': {
        'task': 'standups.tasks.send_follow_up_reminders',
        'schedule': 300.0,  # Run every 5 minutes
    },
    'end-standups': {
        'task': 'standups.tasks.end_standups',
        'schedule': 300.0,  # Run every 5 minutes
    },
    'generate-daily-metrics': {
        'task': 'standups.tasks.generate_daily_metrics',
        'schedule': 3600.0,  # Run every hour
    },
}

app.conf.timezone = 'UTC'


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')