# # tasks.py (Celery tasks)
# from celery import Celery
# from celery.schedules import crontab

# celery_app = Celery(
#     "tasks",
#     broker="redis://redis:6379/0",  # Replace with your Redis broker URL
#     backend="redis://redis:6379/0", # Replace with your Redis backend URL
# )

# celery_app.conf.update(
#     {
#         "worker_concurrency": 1,
#         "task_serializer": "json",
#         "result_serializer": "json",
#         "accept_content": ["json"],
#         "timezone": "UTC",  # Set your desired timezone
#         "beat_schedule": {
#             "daily_task": {
#                 "task": "tasks.daily_task",
#                 "schedule": crontab(hour=0, minute=0),  # Run at midnight (00:00)
#             },
#             "weekly_task": {
#                 "task": "tasks.weekly_task",
#                 "schedule": crontab(day_of_week="sunday", hour=0, minute=0),  # Run every Sunday at midnight
#             },
#             "monthly_task": {
#                 "task": "tasks.monthly_task",
#                 "schedule": crontab(day_of_month=1, hour=0, minute=0),  # Run on the 1st of every month at midnight
#             },
#             "yearly_task": {
#                 "task": "tasks.yearly_task",
#                 "schedule": crontab(month=1, day_of_month=1, hour=0, minute=0), # Run on January 1st at midnight.
#             },
#         },
#     }
# )

# @celery_app.task
# def daily_task():
#     print("Running daily task!")
#     return "Daily task completed"

# @celery_app.task
# def weekly_task():
#     print("Running weekly task!")
#     return "Weekly task completed"

# @celery_app.task
# def monthly_task():
#     print("Running monthly task!")
#     return "Monthly task completed"

# @celery_app.task
# def yearly_task():
#     print("Running yearly task!")
#     return "Yearly task completed"


# tasks.py
from celery import Celery
from celery.schedules import crontab

celery_app = Celery(
    "tasks",
    broker="redis://redis:6379/0",  # Replace with your Redis broker URL
    backend="redis://redis:6379/0", # Replace with your Redis backend URL
)


celery_app.conf.update(
    {
        "worker_concurrency": 1,
        "task_serializer": "json",
        "result_serializer": "json",
        "accept_content": ["json"],
        "timezone": "UTC",  # Set your desired timezone
        "beat_schedule": {
            "daily_task": {
                "task": "tasks.daily_task",
                "schedule": crontab(hour=0, minute=0),  # Run at midnight (00:00)
            },
            "weekly_task": {
                "task": "tasks.weekly_task",
                "schedule": crontab(day_of_week="sunday", hour=0, minute=0),  # Run every Sunday at midnight
            },
            "monthly_task": {
                "task": "tasks.monthly_task",
                "schedule": crontab(day_of_month=1, hour=0, minute=0),  # Run on the 1st of every month at midnight
            },
            "yearly_task": {
                "task": "tasks.yearly_task",
                "schedule": crontab(month_of_year=1, day_of_month=1, hour=0, minute=0), # Run on January 1st at midnight.
            },
            "every_minute_task": {
                "task": "tasks.every_minute_task",
                "schedule": crontab(minute="*"), # Run on every minute
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