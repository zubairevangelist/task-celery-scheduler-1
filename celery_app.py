from celery import Celery

celery = Celery(
    "celery_app",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

celery.conf.timezone = "UTC"
celery.conf.beat_schedule = {}  # This will be populated in beat

# Auto-discover tasks from "tasks.py"
celery.autodiscover_tasks(["tasks"])
