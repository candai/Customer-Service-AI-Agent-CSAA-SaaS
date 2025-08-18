# backend/core/celery.py
import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')

# Explicitly set the broker
app.conf.broker_url = 'redis://127.0.0.1:6379/0'
app.conf.result_backend = 'redis://127.0.0.1:6379/0'

# Then load other settings
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Configure periodic tasks
from celery.schedules import crontab

app.conf.beat_schedule = {
    'aggregate-metrics-hourly': {
        'task': 'apps.analytics.tasks.aggregate_metrics',
        'schedule': crontab(minute=0),  # Run every hour at :00
    },
    'aggregate-daily-metrics': {
        'task': 'apps.analytics.tasks.aggregate_daily_metrics',
        'schedule': crontab(hour=0, minute=5),  # Run daily at 00:05
    },
    'cleanup-old-metrics': {
        'task': 'apps.analytics.tasks.cleanup_old_metrics',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),  # Weekly on Sunday at 2 AM
    },
}

''' 
manual celery beat run

# Open Django shell
python manage.py shell

# Test the task directly
from apps.analytics.tasks import aggregate_metrics
from datetime import datetime, timedelta
from django.utils import timezone

# Run for the last hour manually
result = aggregate_metrics.delay(hours_back=1)
print(f"Task ID: {result.id}")
print(f"Task Status: {result.status}")

# Or run synchronously to see immediate results
aggregate_metrics(hours_back=24)  # Process last 24 hours of data

Celery Flower; http://localhost:5555/worker/celery%40Xs-M1-Pro-Macbook.local#tab-queues
celery -A core flower


Celery Beat
celery -A core beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler

Celery Worker
celery -A core worker -l info

'''