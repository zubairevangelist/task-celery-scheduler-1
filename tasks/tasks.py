# tasks.py
import os
import time
from celery import Celery
from celery.schedules import crontab

from dotenv import load_dotenv
load_dotenv()

POSTGRES_USER = os.getenv("POSTGRES_USER", "myuser")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "mypassword")
POSTGRES_DB = os.getenv("POSTGRES_DB", "mydatabase")
# POSTGRES_HOST = "localhost"
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", 5432)


print("DEBUG:", os.getenv("DEBUG"))

# REDIS_HOST = "localhost"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)

if os.getenv("DEBUG") == "True":
    POSTGRES_HOST = "localhost"
    REDIS_HOST = "localhost"

DATABASE_URL = f"db+postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
print(REDIS_URL)
celery_app = Celery(
    "tasks",
    broker=REDIS_URL,  # Replace with your Redis broker URL
    # backend="redis://redis:6379/0", # Replace with your Redis backend URL
    backend=DATABASE_URL,  # PostgreSQL for results
    # backend="db+postgresql://myuser:mypassword@postgres:5432/mydatabase",  # PostgreSQL for results
)


celery_app.conf.update(
    {
        "worker_concurrency": 1,
        "task_serializer": "json",
        "result_serializer": "json",
        "accept_content": ["json"],
        "timezone": "UTC",  # Set your desired timezone
        "enable_utc":True,
        "beat_schedule": {
            "daily_task": {
                "task": "tasks.tasks.daily_task",
                "schedule": crontab(hour=0, minute=0),  # Run at midnight (00:00)
            },
            "weekly_task": {
                "task": "tasks.tasks.weekly_task",
                "schedule": crontab(day_of_week="sunday", hour=0, minute=0),  # Run every Sunday at midnight
            },
            "monthly_task": {
                "task": "tasks.tasks.monthly_task",
                "schedule": crontab(day_of_month=1, hour=0, minute=0),  # Run on the 1st of every month at midnight
            },
            "yearly_task": {
                "task": "tasks.tasks.yearly_task",
                "schedule": crontab(month_of_year=1, day_of_month=1, hour=0, minute=0), # Run on January 1st at midnight.
            },
            "every_minute_task": {
                "task": "tasks.tasks.every_minute_task",
                "schedule": crontab(hour="*"), # Run on every minute
            },
        },
    }
)

@celery_app.task
def hello_world():
    print("Hello, World! from Celery!")
    return "Hello, World! task completed"

@celery_app.task
def daily_task():
    print("Running daily task!")
    return "Daily task completed"

@celery_app.task
def weekly_task():
    print("Running weekly task!")
    return "Weekly task completed"

@celery_app.task
def monthly_task():
    print("Running monthly task!")
    return "Monthly task completed"

@celery_app.task
def yearly_task():
    print("Running yearly task!")
    return "Yearly task completed"

@celery_app.task
def every_minute_task():
    print("Running every minute task!")
    # return "every minute task completed"
    return {"message": "Every minute task completed"}

@celery_app.task
def on_time_task(task_id: int, user_id: str):
    """
    This task will run at the scheduled time and execute logic.
    """
    print(f"Executing Task on given time")
    # Simulate processing time
    # time.sleep(2)
    return {"message": "On time task completed"}



@celery_app.task
def execute_scheduled_task():
    """Executes the scheduled task"""
    print(f"Executing task for user")
    return {"status": "Completed", "task_id": "id"}

