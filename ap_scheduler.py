# import uvicorn
# from fastapi import FastAPI, BackgroundTasks
# from apscheduler.schedulers.background import BackgroundScheduler
# from apscheduler.triggers.cron import CronTrigger
# from datetime import datetime
# import pytz
#
# app = FastAPI()
# scheduler = BackgroundScheduler(timezone="UTC")
# scheduler.start()
#
#
# def scheduled_task(task_id: str):
#     print(f"Executing task {task_id} at {datetime.now(pytz.UTC)} UTC")
#
#
# @app.post("/schedule-task/")
# def schedule_task(
#     task_id: str,
#     date: str,  # YYYY-MM-DD
#     time: str,  # HH:MM (24-hour format)
#     frequency: str  # daily, weekly, monthly, yearly
# ):
#     user_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
#     user_datetime = user_datetime.replace(tzinfo=pytz.UTC)  # Ensure UTC
#
#     if frequency == "daily":
#         trigger = CronTrigger(hour=user_datetime.hour, minute=user_datetime.minute)
#     elif frequency == "weekly":
#         trigger = CronTrigger(day_of_week=user_datetime.weekday(), hour=user_datetime.hour, minute=user_datetime.minute)
#     elif frequency == "monthly":
#         trigger = CronTrigger(day=user_datetime.day, hour=user_datetime.hour, minute=user_datetime.minute)
#     elif frequency == "yearly":
#         trigger = CronTrigger(month=user_datetime.month, day=user_datetime.day, hour=user_datetime.hour, minute=user_datetime.minute)
#     else:
#         return {"error": "Invalid frequency. Choose daily, weekly, monthly, or yearly."}
#
#     scheduler.add_job(scheduled_task, trigger, args=[task_id], id=task_id, replace_existing=True)
#
#     return {"message": f"Task {task_id} scheduled {frequency} at {user_datetime}"}
#
#
#
# @app.get("/tasks/")
# def list_scheduled_tasks():
#     jobs = scheduler.get_jobs()
#     return [{"id": job.id, "next_run_time": job.next_run_time} for job in jobs]
#
#
# @app.delete("/remove-task/{task_id}")
# def remove_task(task_id: str):
#     scheduler.remove_job(task_id)
#     return {"message": f"Task {task_id} removed"}
#
#
# if __name__ == '__main__':
#     uvicorn.run(app, host='0.0.0.0', port=8000)