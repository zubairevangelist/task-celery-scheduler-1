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
from pydantic import BaseModel, EmailStr, IPvAnyAddress, constr, Field
import datetime
import uvicorn
from tasks.tasks import daily_task, every_minute_task, weekly_task, monthly_task, yearly_task
from config import settings


from fastapi import FastAPI, HTTPException, Depends
from fastapi import FastAPI
from contextlib import asynccontextmanager
from sqlmodel import SQLModel, Field, create_engine, Session, select
from typing import Optional
import datetime



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
    task_frequency: str = Field(..., regex="^(daily|weekly|monthly|yearly)$")
    task_title: str
    task_date: datetime.date
    task_time: datetime.time
    user_id: str

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
    
    # # Create DB engine and session
    # engine = create_engine("postgresql://myuser:mypassword@postgres/mydatabase")
    # SessionLocal = sessionmaker(bind=engine)
    # session = SessionLocal()
    from db.models import session
    tasks = session.query(CeleryTaskmeta).filter()

    for task in tasks:
        print(task.id, task.status, task.task_id)

    return {"message": "Celery scheduled tasks"}







# Database Connection
DATABASE_URL = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
# DATABASE_URL = "postgresql://myuser:mypassword@postgres:5432/mydatabase"
engine = create_engine(DATABASE_URL, echo=True)

#  Define the SQLModel
class ScheduleTasks(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    task_ip: str = Field(nullable=False)
    task_domain: str = Field(nullable=False)
    task_frequency: str = Field(nullable=False)
    task_title: str = Field(nullable=False)
    task_date: datetime.date = Field(nullable=False)
    task_time: datetime.time = Field(nullable=False)
    user_id: str = Field(nullable=False)




def get_session():
    with Session(engine) as session:
        yield session

@app.post("/tasks/", response_model=ScheduleTasks)
def create_task(task: ScheduleTasks, session: Session = Depends(get_session)):
    session.add(task)
    session.commit()
    session.refresh(task)
    return task

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
