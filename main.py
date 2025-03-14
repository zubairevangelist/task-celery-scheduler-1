import os
import re
from uuid import UUID
import uuid

from celery import current_app
from fastapi import BackgroundTasks, FastAPI, HTTPException
import httpx
from pydantic import BaseModel, EmailStr, IPvAnyAddress, constr, Field, field_validator
import datetime
import pytz
import requests
import uvicorn
from tasks.tasks import daily_task, every_minute_task, on_time_task, weekly_task, monthly_task, yearly_task

from fastapi import FastAPI, HTTPException, Depends
from fastapi import FastAPI
from contextlib import asynccontextmanager
from sqlmodel import SQLModel, Field, create_engine, Session, select
from typing import Annotated, Optional
import datetime
from celery.schedules import crontab

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

POSTGRES_USER = os.getenv("POSTGRES_USER", "myuser")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "mypassword")
POSTGRES_DB = os.getenv("POSTGRES_DB", "mydatabase")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", 5432)



REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)

if os.getenv("DEBUG") == "True":
    POSTGRES_HOST = "localhost"
    REDIS_HOST = "localhost"

from sqlmodel import SQLModel


# Database Connection
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
# DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
print(DATABASE_URL)
# DATABASE_URL = "postgresql://myuser:mypassword@postgres:5432/mydatabase"
engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

create_db_and_tables()


# app = FastAPI()



# Create Database Tables on Startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Creating database tables...")
    SQLModel.metadata.create_all(engine)
    print("Database tables are ready.")
    yield  # Continue running the app
    print("Shutting down...")

# FastAPI App with Lifespan
app = FastAPI(lifespan=lifespan)



class ScheduleTaskRequest(BaseModel):
    task_ip: IPvAnyAddress
    task_domain: str  
    task_api: str  
    task_frequency: str = Field(..., regex="^(daily|weekly|monthly|yearly)$")
    task_date: Annotated[datetime.date, Field()]  
    task_time: Annotated[datetime.time, Field()]  
    task_priority: str = Field(..., regex="^(low|medium|high)$")
    task_title: str
    user_id: str
    task_id: str   

    @field_validator("task_domain")
    @classmethod
    def validate_domain(cls, value: str):
        domain_pattern = re.compile(
            r"^(?!:\/\/)([a-zA-Z0-9-]+\.)*[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$"
        )
        
        if not domain_pattern.fullmatch(value):
            raise ValueError("Invalid domain or subdomain. Example: example.com or sub.example.com")

        return value  

#  Define the SQLModel
class ScheduleTasks(SQLModel, table=True):
    __tablename__ = "schedule_tasks"
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    task_ip: str = Field(nullable=True)
    task_api: str = Field(nullable=True)
    task_domain: str = Field(nullable=True)
    task_frequency: str = Field(..., regex="^(daily|weekly|monthly|yearly)$", nullable=True)
    task_title: str = Field(nullable=True)
    task_priority: Optional[str] = Field(default=None, regex="^(low|medium|high)$")
    task_date: Optional[datetime.date] = Field(default=None)
    task_time: Optional[datetime.time] = Field(default=None)
    user_id: str = Field(nullable=True)



def get_session():
    with Session(engine) as session:
        yield session


@app.get("/")
async def root():
    return {"message": "Welcome to the scheduler api"}


@app.post("/tasks/", response_model=ScheduleTasks)
def create_task(request: ScheduleTaskRequest, session: Session = Depends(get_session)):
    try:

        # Convert user-provided date & time to UTC
        task_datetime = datetime.datetime.combine(request.task_date, request.task_time)
        task_datetime = task_datetime.replace(tzinfo=datetime.timezone.utc)
        
        
        # Validate if the scheduled time is in the future
        if task_datetime <= datetime.datetime.now(datetime.timezone.utc):
            raise HTTPException(status_code=400, detail="Scheduled time must be in the future")


        # Validate input and map Pydantic request to SQLAlchemy model
        task = ScheduleTasks(
            task_ip=str(request.task_ip),
            task_api=request.task_api,
            task_domain=request.task_domain,
            task_frequency=request.task_frequency,
            task_priority=request.task_priority,
            task_title=request.task_title,
            task_date=request.task_date,
            task_time=request.task_time,
            user_id=request.user_id,
        )

        # Save to DB
        session.add(task)
        session.commit()
        session.refresh(task)

        if request.task_date != "" and request.task_time != "":
            # **Schedule Celery Task**
            print(f"Scheduled Task On given time %s", task_datetime)    
            task_result = on_time_task.apply_async(args=[101, "user123"], eta=task_datetime)

            print(f"Scheduled Task ID: {task_result.id}")
            # return {"message": "Task Scheduled", "task_id": task_result.id}
        
        # Trigger Celery Task Based on Frequency
        task_mapping = {
            "daily": daily_task,
            "weekly": weekly_task,
            "monthly": monthly_task,
            "yearly": yearly_task,
            "every-minute": every_minute_task
        }

        if task.task_frequency in task_mapping:
            task_mapping[task.task_frequency].delay()

        # # Call External API (With Error Handling)
        # url = "https://ingress.ip.attackinsights.dev/ip-scan-all"
        # data = {
        #     "task_ip": task.task_ip,
        #     "user_id": task.user_id
        # }

        # try:
        #     with httpx.Client(timeout=10) as client:
        #         response = client.post(url, json=data)
        #         response.raise_for_status()  # Raises an exception for 4xx/5xx errors
        #         api_response = response.json()
        # except httpx.RequestError as e:
        #     raise HTTPException(status_code=502, detail=f"External API request failed: {str(e)}")

        return task

    except Exception as e:
        session.rollback()  # Rollback if an error occurs
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

    finally:
        session.close()  # Ensure session is closed properly
       # Print response JSON


    # return task

@app.get("/tasks/", response_model=list[ScheduleTasks])
def get_tasks(session: Session = Depends(get_session)):
    tasks = session.exec(select(ScheduleTasks)).all()
    return tasks


@app.get("/tasks/{task_id}", response_model=ScheduleTasks)
def get_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(ScheduleTasks, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.put("/tasks/{task_id}", response_model=ScheduleTasks)
def update_task(task_id: int, updated_task: ScheduleTasks, session: Session = Depends(get_session)):
    task = session.get(ScheduleTasks, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    for key, value in updated_task.dict(exclude_unset=True).items():
        setattr(task, key, value)

    session.commit()
    session.refresh(task)
    return task


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(ScheduleTasks, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    session.delete(task)
    session.commit()
    return {"message": "Task deleted successfully"}


@app.post("/schedule-task/")
async def schedule_task_api(request: ScheduleTaskRequest, background_tasks: BackgroundTasks):
    """
    API to schedule a task with a specific time and frequency.
    """
    print("in schedule task api")
    background_tasks.add_task(
        schedule_task, request.task_id, request.user_id, request.task_date, request.task_time, request.task_frequency
    )
    return {"message": "Task scheduled successfully", "task_id": request.task_id}





def schedule_task(task_id, user_id, task_date, task_time, frequency):
    """
    Dynamically schedules a Celery task based on user-provided date, time, and frequency.
    """
    print("in schedule task function")
    # Convert user-provided date & time to UTC
    task_datetime = datetime.datetime.combine(task_date, task_time)
    task_datetime = task_datetime.replace(tzinfo=datetime.timezone.utc)
    
    
    # Validate if the scheduled time is in the future
    if task_datetime <= datetime.datetime.now(datetime.timezone.utc):
        raise HTTPException(status_code=400, detail="Scheduled time must be in the future")


    hour, minute = task_datetime.hour, task_datetime.minute
    day, month, weekday = task_datetime.day, task_datetime.month, task_datetime.weekday()
    print("minute", minute, "hour", hour,  "day", day, "month", month, "weekday", weekday)
    # Set scheduling rules
    if frequency == "daily":
        schedule = crontab(hour=hour, minute=minute)
    elif frequency == "weekly":
        schedule = crontab(day_of_week=weekday, hour=hour, minute=minute)
    elif frequency == "monthly":
        schedule = crontab(day_of_month=day, hour=hour, minute=minute)
    elif frequency == "yearly":
        schedule = crontab(month_of_year=month, day_of_month=day, hour=hour, minute=minute)
    else:
        raise HTTPException(status_code=400, detail="Invalid frequency. Choose from daily, weekly, monthly, yearly.")

    from tasks.tasks import celery_app
    # Add task to Celery Beat schedule
    current_app.conf.beat_schedule[f"task_{task_id}"] = {
        "task": "tasks.tasks.execute_scheduled_task",
        "schedule": schedule,
    }
    print(f"Scheduled Task {task_id} at {task_datetime} with frequency {frequency}")


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
