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
import os
from fastapi import FastAPI, HTTPException
import httpx
from pydantic import BaseModel, EmailStr, IPvAnyAddress, constr, Field
import datetime
import requests
import uvicorn
from tasks.tasks import daily_task, every_minute_task, weekly_task, monthly_task, yearly_task
# from config import settings


from fastapi import FastAPI, HTTPException, Depends
from fastapi import FastAPI
from contextlib import asynccontextmanager
from sqlmodel import SQLModel, Field, create_engine, Session, select
from typing import Optional
import datetime


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
    task_domain: EmailStr  
    task_api: str  
    task_frequency: str = Field(..., regex="^(daily|weekly|monthly|yearly)$")
    task_date: datetime.date
    task_time: datetime.time
    task_priority: str = Field(..., regex="^(low|medium|high)$")
    task_title: str
    user_id: str

# @app.post("/schedule_task")
# async def schedule_task(request: ScheduleTaskRequest):
    
#     if request.task_frequency == "daily":
#         daily_task.delay()
#     elif request.task_frequency == "weekly":
#         weekly_task.delay()
#     elif request.task_frequency == "monthly":
#         monthly_task.delay()
#     elif request.task_frequency == "yearly":
#         yearly_task.delay()
#     elif request.task_frequency == "every-minute":
#         every_minute_task.delay()
        

#     return {"message": "Task has been scheduled!"}
   

# @app.get("/daily")
# async def trigger_daily():
#   daily_task.delay()
#   return {"message": "Daily task triggered"}

# @app.get("/weekly")
# async def trigger_weekly():
#     weekly_task.delay()
#     return {"message": "Weekly task triggered"}

# @app.get("/monthly")
# async def trigger_monthly():
#     monthly_task.delay()
#     return {"message": "Monthly task triggered"}

# @app.get("/yearly")
# async def trigger_yearly():
#     yearly_task.delay()
#     return {"message": "Yearly task triggered"}

from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class CeleryTaskmeta(Base):
    __tablename__ = "celery_taskmeta"
    id = Column(Integer, primary_key=True)
    task_id = Column(String(100))
    status = Column(String(10))


@app.get("/")
async def root():

    return {"message": "Welcome to the scheduler api"}


# Database Connection
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
# DATABASE_URL = "postgresql://myuser:mypassword@postgres:5432/mydatabase"
engine = create_engine(DATABASE_URL, echo=True)


from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

#  Define the SQLModel
class ScheduleTasks(SQLModel, table=True):
    __tablename__ = "schedule_tasks"
    id: Optional[int] = Field(default=None, primary_key=True)
    task_ip: str = Field(nullable=True)
    # task_api: str = Field(nullable=True)
    task_domain: str = EmailStr
    task_frequency: str = Field(..., regex="^(daily|weekly|monthly|yearly)$", nullable=True)
    task_title: str = Field(nullable=True)
    task_priority: Optional[str] = Field(default=None, regex="^(low|medium|high)$")
    task_date: datetime.date = Field(nullable=True)
    task_time: datetime.time = Field(nullable=True)
    user_id: str = Field(nullable=True)


    # task_ip: IPvAnyAddress
    # task_domain: EmailStr  
    # task_api: str  
    # task_frequency: str = Field(..., regex="^(daily|weekly|monthly|yearly)$")
    # task_date: datetime.date
    # task_time: datetime.time
    # task_priority = str = Field(..., regex="^(low|medium|high)$")
    # task_title: str
    # user_id: str



def get_session():
    with Session(engine) as session:
        yield session

@app.post("/tasks/", response_model=ScheduleTasks)
def create_task(request: ScheduleTaskRequest, session: Session = Depends(get_session)):
    try:
        # Validate input and map Pydantic request to SQLAlchemy model
        task = ScheduleTasks(
            task_ip=str(request.task_ip),
            task_api=request.task_api,
            task_domain=request.task_domain,
            task_frequency=request.task_frequency,
            task_title=request.task_title,
            task_date=request.task_date,
            task_time=request.task_time,
            user_id=request.user_id,
        )

        # Save to DB
        session.add(task)
        session.commit()
        session.refresh(task)

        # Trigger Celery Task Based on Frequency
        task_mapping = {
            "daily": daily_task,
            "weekly": weekly_task,
            "monthly": monthly_task,
            "yearly": yearly_task,
            "every-minute": every_minute_task,
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


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
