import datetime
import os
import re
import uuid
from contextlib import asynccontextmanager
from typing import Annotated, Optional

import httpx
import pytz
import uvicorn
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi import HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, IPvAnyAddress, field_validator
from sqlmodel import Field, create_engine, Session, select

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with specific origins if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# APScheduler job store configuration (PostgreSQL)
jobstores = {
    "default": SQLAlchemyJobStore(url=DATABASE_URL)
}

scheduler = BackgroundScheduler(jobstores=jobstores, timezone="UTC")
scheduler.start()


def scheduled_task(task_id: str):
    print(f"Executing task {task_id} at {datetime.datetime.now(pytz.UTC)} UTC")

@app.get("/")
async def root():
    return {"message": "Welcome to the scheduler api"}



@app.get("/tasks/")
def list_scheduled_tasks():
    jobs = scheduler.get_jobs()
    return [{"id": job.id, "next_run_time": job.next_run_time} for job in jobs]


@app.delete("/remove-task/{task_id}")
def remove_task(task_id: str):
    scheduler.remove_job(task_id)
    return {"message": f"Task {task_id} removed"}




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
    task_id: uuid.UUID

    @field_validator("task_domain")
    @classmethod
    def validate_domain(cls, value: str):
        domain_pattern = re.compile(
            r"^(?!:\/\/)([a-zA-Z0-9-]+\.)*[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$"
        )
        
        if not domain_pattern.fullmatch(value):
            raise ValueError("Invalid domain or subdomain. Example: example.com or sub.example.com")

        return value

    @field_validator("task_frequency")
    @classmethod
    def validate_task_frequency(cls, value: str):
        allowed_frequencies = {"daily", "weekly", "monthly", "yearly"}
        if value.lower() not in allowed_frequencies:
            raise ValueError(f"Invalid task_frequency. Allowed values: {allowed_frequencies}")
        return value.lower()  # Normalize input to lowercase

    @field_validator("task_priority")
    @classmethod
    def validate_task_priority(cls, value: str):
        allowed_priorities = {"low", "medium", "high"}
        if value.lower() not in allowed_priorities:
            raise ValueError(f"Invalid task_priority. Allowed values: {allowed_priorities}")
        return value.lower()  # Normalize input to lowercase


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
    task_id: uuid.UUID = Field(nullable=True)


def get_session():
    with Session(engine) as session:
        yield session



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
            task_id=request.task_id
        )

        # Save to DB
        session.add(task)
        session.commit()
        session.refresh(task)

        # user_datetime = datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        # user_datetime = user_datetime.replace(tzinfo=pytz.UTC)  # Ensure UTC

        frequency = request.task_frequency
        user_datetime = task_datetime

        if frequency == "daily":
            trigger = CronTrigger(hour=user_datetime.hour, minute=user_datetime.minute)
        elif frequency == "weekly":
            trigger = CronTrigger(day_of_week=user_datetime.weekday(), hour=user_datetime.hour,
                                  minute=user_datetime.minute)
        elif frequency == "monthly":
            trigger = CronTrigger(day=user_datetime.day, hour=user_datetime.hour, minute=user_datetime.minute)
        elif frequency == "yearly":
            trigger = CronTrigger(month=user_datetime.month, day=user_datetime.day, hour=user_datetime.hour,
                                  minute=user_datetime.minute)
        else:
            return {"error": "Invalid frequency. Choose daily, weekly, monthly, or yearly."}

        scheduler.add_job(scheduled_task, trigger, args=[task.task_id], id=str(task.task_id), replace_existing=True)

        # Call External API (With Error Handling)
        # call_to_ingress(task)

        return task

    except Exception as e:
        session.rollback()  # Rollback if an error occurs
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

    finally:
        session.close()  # Ensure session is closed properly
       # Print response JSON


def call_to_ingress(task: ScheduleTasks):
    # Call External API (With Error Handling)
    url = "https://ingress.ip.attackinsights.dev/ip-scan-all"
    data = {
        "ip": task.task_ip,
        "user_id": task.user_id
    }

    try:
        with httpx.Client(timeout=10) as client:
            response = client.post(url, json=data)
            response.raise_for_status()  # Raises an exception for 4xx/5xx errors
            api_response = response.json()
            print(api_response)
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"External API request failed: {str(e)}")


# @app.get("/tasks-in-db/", response_model=list[ScheduleTasks])
# def get_tasks(session: Session = Depends(get_session)):
#     tasks = session.exec(select(ScheduleTasks)).all()
#     return tasks


# @app.get("/tasks/{task_id}", response_model=ScheduleTasks)
# def get_task(task_id: int, session: Session = Depends(get_session)):
#     task = session.get(ScheduleTasks, task_id)
#     if not task:
#         raise HTTPException(status_code=404, detail="Task not found")
#     return task


# @app.put("/tasks/{task_id}", response_model=ScheduleTasks)
# def update_task(task_id: int, updated_task: ScheduleTasks, session: Session = Depends(get_session)):
#     task = session.get(ScheduleTasks, task_id)
#     if not task:
#         raise HTTPException(status_code=404, detail="Task not found")
    
#     for key, value in updated_task.dict(exclude_unset=True).items():
#         setattr(task, key, value)

#     session.commit()
#     session.refresh(task)
#     return task


# @app.delete("/tasks/{task_id}")
# def delete_task(task_id: int, session: Session = Depends(get_session)):
#     task = session.get(ScheduleTasks, task_id)
#     if not task:
#         raise HTTPException(status_code=404, detail="Task not found")
    
#     session.delete(task)
#     session.commit()
#     return {"message": "Task deleted successfully"}

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
