from pydantic import BaseModel, Field
from typing import Optional, List

class HabitSchema(BaseModel):
    """
    Schema representing user's target habit parameters.
    """
    name: str = Field(..., min_length=1, max_length=100, description="Name of the habit to alter")
    description: Optional[str] = Field(None, max_length=500, description="Brief context details about the habit")
    triggers: Optional[str] = Field(None, max_length=500, description="Primary circumstances that trigger the habit")
    motivation: Optional[str] = Field(None, max_length=500, description="Why the user wants to break the habit")
    target_reduction: Optional[str] = Field(None, max_length=100, description="Clear reduction metrics goal")

class LogSchema(BaseModel):
    """
    Daily check-in log details recorded in browser localStorage.
    """
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Date string in YYYY-MM-DD format")
    metric_value: float = Field(..., ge=0.0, description="Numeric consumption metrics level (e.g. minutes, quantity)")
    craving_level: int = Field(..., ge=1, le=10, description="Urge/craving intensity level scaled 1 to 10")
    slip_up: bool = Field(False, description="Flag indicating if the user engaged in the target habit")
    notes: Optional[str] = Field(None, max_length=1000, description="Reflections on logs/triggers during the day")

class MessageSchema(BaseModel):
    """
    Stateless conversational message format for history context.
    """
    sender: str = Field(..., pattern="^(user|coach)$", description="Identifies conversation speaker role")
    message: str = Field(..., min_length=1, description="Message body content")

# Stateless Request Payloads
class ChatRequest(BaseModel):
    """
    Request model containing current habit configuration, messaging history,
    and latest text message to process AI response.
    """
    habit: HabitSchema
    history: List[MessageSchema]
    message: str = Field(..., min_length=1)
    is_sos: bool = Field(False, description="SOS emergency grounding request flag")

class NudgeRequest(BaseModel):
    """
    Payload for fetching daily tailored nudges.
    """
    habit: HabitSchema
    recent_logs: List[LogSchema]

class AnalysisRequest(BaseModel):
    """
    Payload for fetching weekly behavioral review reports.
    """
    habit: HabitSchema
    recent_logs: List[LogSchema]

# Responses
class ChatMessageResponse(BaseModel):
    """
    Coaching chatbot reply response structure.
    """
    sender: str
    message: str
    timestamp: str

class NudgeResponse(BaseModel):
    """
    Daily nudge response text.
    """
    nudge: str

class AnalysisResponse(BaseModel):
    """
    Weekly behavioral analysis Markdown text.
    """
    analysis: str
