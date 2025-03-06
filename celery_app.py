# from celery import Celery

# celery = Celery(
#     "celery_app",
#     broker="redis://localhost:6379/0",
#     # backend="redis://redis:6379/0", # Replace with your Redis backend URL
#     backend="db+postgresql://myuser:mypassword@postgres:5432/mydatabase"  # PostgreSQL for results
# )

# celery.conf.timezone = "UTC"
# celery.conf.beat_schedule = {}  # This will be populated in beat

# # Auto-discover tasks from "tasks.py"
# celery.autodiscover_tasks(["tasks"])
