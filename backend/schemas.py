from pydantic import BaseModel, Field
from typing import Optional, List

class HabitSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    triggers: Optional[str] = Field(None, max_length=500)
    motivation: Optional[str] = Field(None, max_length=500)
    target_reduction: Optional[str] = Field(None, max_length=100)

class LogSchema(BaseModel):
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    metric_value: float = Field(..., ge=0.0)
    craving_level: int = Field(..., ge=1, le=10)
    slip_up: bool = Field(False)
    notes: Optional[str] = Field(None, max_length=1000)

class MessageSchema(BaseModel):
    sender: str = Field(..., pattern="^(user|coach)$")
    message: str = Field(..., min_length=1)

# Stateless Request Payloads
class ChatRequest(BaseModel):
    habit: HabitSchema
    history: List[MessageSchema]
    message: str = Field(..., min_length=1)
    is_sos: bool = Field(False)

class NudgeRequest(BaseModel):
    habit: HabitSchema
    recent_logs: List[LogSchema]

class AnalysisRequest(BaseModel):
    habit: HabitSchema
    recent_logs: List[LogSchema]

# Responses
class ChatMessageResponse(BaseModel):
    sender: str
    message: str
    timestamp: str

class NudgeResponse(BaseModel):
    nudge: str

class AnalysisResponse(BaseModel):
    analysis: str
