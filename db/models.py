from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class CeleryTaskmeta(Base):
    __tablename__ = "celery_taskmeta"
    id = Column(Integer, primary_key=True)
    task_id = Column(String(100))
    status = Column(String(10))


engine = create_engine("postgresql://myuser:mypassword@postgres/mydatabase")
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()


from sqlalchemy import Column, Integer, String, Date, Time, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select

class ScheduleTasks(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    task_ip = Column(String, nullable=False)
    task_domain = Column(String, nullable=False)
    task_frequency = Column(String, nullable=False)
    task_title = Column(String, nullable=False)
    task_date = Column(Date, nullable=False)
    task_time = Column(Time, nullable=False)
    user_id = Column(String, nullable=False)
    task_id = Column(String, nullable=False)
