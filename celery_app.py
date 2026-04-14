import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# Create Celery app
app = Celery('finance-tracker')

# Load settings from Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django app configs
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

#to run celery celery -A celery_app worker --loglevel=info
app.conf.beat_schedule = {
    'send-payment-reminders': {
        'task': 'payments.tasks.send_payment_reminders',
        'schedule': crontab(hour=9, minute=0),  # Run daily at 9 AM
    },
}