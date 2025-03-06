# from fastapi import FastAPI
# import uvicorn
# from tasks import daily_task

# app = FastAPI()

# @app.get("/")
# def read_root():
#     return {"message": "Hello, FastAPI with Celery"}

# @app.get("/run-task")
# def run_task():
#     daily_task.delay()  # Manually trigger the task
#     return {"message": "Task has been scheduled!"}


# if __name__ == '__main__':
#     uvicorn.run(app, host='0.0.0.0', port=5000)



# main.py (FastAPI - optional, for API interaction)
from fastapi import FastAPI
from pydantic import BaseModel
from tasks import daily_task, every_minute_task, weekly_task, monthly_task, yearly_task

app = FastAPI()

class ScheduleTaskRequest(BaseModel):
    task_scope: str
    task_frequency: str

@app.post("/schedule_task")
async def schedule_task(request: ScheduleTaskRequest):
    
    if request.task_frequency == "daily":
        daily_task.delay()
    elif request.task_frequency == "weekly":
        weekly_task.delay()
    elif request.task_frequency == "monthly":
        monthly_task.delay()
    elif request.task_frequency == "yearly":
        yearly_task.delay()
    elif request.task_frequency == "every-minute":
        every_minute_task.delay()
        

    return {"message": "Task has been scheduled!"}
   

@app.get("/daily")
async def trigger_daily():
  daily_task.delay()
  return {"message": "Daily task triggered"}

@app.get("/weekly")
async def trigger_weekly():
    weekly_task.delay()
    return {"message": "Weekly task triggered"}

@app.get("/monthly")
async def trigger_monthly():
    monthly_task.delay()
    return {"message": "Monthly task triggered"}

@app.get("/yearly")
async def trigger_yearly():
    yearly_task.delay()
    return {"message": "Yearly task triggered"}

@app.get("/")
async def root():
    return {"message": "Celery scheduled tasks"}



# # main.py (Optional FastAPI example to trigger the task)
# from fastapi import FastAPI
# from tasks import hello_world

# app = FastAPI()

# @app.get("/hello")
# async def trigger_hello():
#     hello_world.delay()  # Schedule the task to run in the background
#     return {"message": "Hello task triggered"}

# @app.get("/")
# async def root():
#     return {"message": "Celery Hello World"}
