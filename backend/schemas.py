from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime

# Habit Schemas
class HabitBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="The habit to change")
    description: Optional[str] = Field(None, max_length=500, description="Short summary/description")
    triggers: Optional[str] = Field(None, max_length=500, description="Identified triggers")
    motivation: Optional[str] = Field(None, max_length=500, description="Reasons for wanting to break the habit")
    target_reduction: Optional[str] = Field(None, max_length=100, description="Reduction goals, e.g., '30 mins/day'")

class HabitCreate(HabitBase):
    pass

class HabitResponse(HabitBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Log Schemas
class LogBase(BaseModel):
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="YYYY-MM-DD format")
    metric_value: float = Field(..., ge=0.0, description="E.g., quantity of habit consumed or time spent in minutes")
    craving_level: int = Field(..., ge=1, le=10, description="Craving scale from 1 (lowest) to 10 (highest)")
    slip_up: bool = Field(False, description="Did the user experience a slip up?")
    notes: Optional[str] = Field(None, max_length=1000)

class LogCreate(LogBase):
    pass

class LogResponse(LogBase):
    id: int
    habit_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Chat Message Schemas
class ChatMessageBase(BaseModel):
    sender: str = Field(..., pattern="^(user|coach)$")
    message: str = Field(..., min_length=1)

class ChatMessageCreate(ChatMessageBase):
    pass

class ChatMessageResponse(ChatMessageBase):
    id: int
    habit_id: int
    timestamp: datetime

    class Config:
        from_attributes = True

# Chat request schema
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    is_sos: bool = Field(False, description="Whether the emergency/SOS urge mode is triggered")

# Nudge & Insights Schemas
class NudgeResponse(BaseModel):
    nudge: str

class AnalysisResponse(BaseModel):
    analysis: str
