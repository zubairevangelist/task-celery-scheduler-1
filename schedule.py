from celery.schedules import crontab
from celery_app import celery

celery.conf.beat_schedule = {
    "print-hello-every-minute": {
        "task": "tasks.print_hello",
        "schedule": crontab(minute="*"),  # Runs every minute
    },
}
