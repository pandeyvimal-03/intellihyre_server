import sys
import os

# Add 'server' directory to sys.path so 'app' can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import select, Column, Integer, String, DateTime, Enum
from app.core.config import settings
import enum

Base = declarative_base()

class InterviewStatus(str, enum.Enum):
    PENDING = "PENDING"
    ONGOING = "ONGOING"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"

class Interview(Base):
    __tablename__ = "interviews"
    id = Column(Integer, primary_key=True)
    token = Column(String, unique=True)
    status = Column(Enum(InterviewStatus))
    scheduled_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))

async def check_interview():
    engine = create_async_engine(settings.DATABASE_URL)
    session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with session_maker() as db:
        token = "a68b926b-dbc1-4f83-8637-b88df761c19a"
        result = await db.execute(select(Interview).where(Interview.token == token))
        interview = result.scalar_one_or_none()
        
        if interview:
            print(f"Interview ID: {interview.id}")
            print(f"Status: {interview.status}")
            print(f"Expires at: {interview.expires_at}")
        else:
            print("Interview not found.")

if __name__ == "__main__":
    asyncio.run(check_interview())
