import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

if os.environ.get("VERCEL") == "1":
    default_db = "sqlite:////tmp/aura.db"
else:
    default_db = "sqlite:///./aura.db"

DATABASE_URL = os.environ.get("DATABASE_URL", default_db)

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Habit(Base):
    __tablename__ = "habits"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    triggers = Column(String, nullable=True)
    motivation = Column(String, nullable=True)
    target_reduction = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    logs = relationship("Log", back_populates="habit", cascade="all, delete-orphan")
    chats = relationship("ChatMessage", back_populates="habit", cascade="all, delete-orphan")

class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    habit_id = Column(Integer, ForeignKey("habits.id"), nullable=False)
    date = Column(String, nullable=False)  # Format: YYYY-MM-DD
    metric_value = Column(Float, nullable=False)
    craving_level = Column(Integer, nullable=False)  # 1-10 scale
    slip_up = Column(Boolean, default=False)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    habit = relationship("Habit", back_populates="logs")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    habit_id = Column(Integer, ForeignKey("habits.id"), nullable=False)
    sender = Column(String, nullable=False)  # "user" or "coach"
    message = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    habit = relationship("Habit", back_populates="chats")

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
