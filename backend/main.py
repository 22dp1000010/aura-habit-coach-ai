import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import List

from . import database, schemas, crud, ai

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize the database tables
    database.init_db()
    
    # Check Groq API configuration
    api_key = ai.get_api_key()
    if not api_key:
        print("[WARNING] GROQ_API_KEY is not set. GenAI capabilities will fail at request time.")
    else:
        is_valid = await ai.check_api_key_valid()
        if is_valid:
            print("[INFO] GROQ_API_KEY is configured and validated successfully.")
        else:
            print("[WARNING] GROQ_API_KEY is set but failed validation check (unauthorized or network issues).")
            
    yield
    # Shutdown logic (none required)

app = FastAPI(
    title="Aura: AI Habit Coach API",
    description="Backend API for habit tracking and CBT-based cognitive coaching",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify Vercel deployment URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helpers
def verify_active_habit(db: Session = Depends(database.get_db)) -> database.Habit:
    habit = crud.get_latest_habit(db)
    if not habit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No habit configured. Please configure your habit profile first."
        )
    return habit

# Endpoints
@app.get("/api/health")
async def health_check(db: Session = Depends(database.get_db)):
    db_status = "healthy"
    try:
        # Simple query to verify DB connection
        db.execute(text("SELECT 1")).scalar()
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        
    api_key = ai.get_api_key()
    ai_status = "configured" if api_key else "missing"
    
    return {
        "status": "ok",
        "database": db_status,
        "ai_service": ai_status
    }

@app.get("/api/habit", response_model=schemas.HabitResponse)
def get_habit(db: Session = Depends(database.get_db)):
    habit = crud.get_latest_habit(db)
    if not habit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active habit setup found."
        )
    return habit

@app.post("/api/habit", response_model=schemas.HabitResponse)
def setup_habit(habit_in: schemas.HabitCreate, db: Session = Depends(database.get_db)):
    # Delete existing habit configurations to keep the experience focused on one habit
    existing = crud.get_latest_habit(db)
    if existing:
        crud.delete_habit(db, existing.id)
    return crud.create_habit(db, habit_in)

@app.get("/api/logs", response_model=List[schemas.LogResponse])
def get_logs(habit: database.Habit = Depends(verify_active_habit), db: Session = Depends(database.get_db)):
    return crud.get_logs(db, habit.id)

@app.post("/api/logs", response_model=schemas.LogResponse)
def log_progress(log_in: schemas.LogCreate, habit: database.Habit = Depends(verify_active_habit), db: Session = Depends(database.get_db)):
    return crud.create_log(db, log_in, habit.id)

@app.get("/api/chat/history", response_model=List[schemas.ChatMessageResponse])
def get_chat_history(habit: database.Habit = Depends(verify_active_habit), db: Session = Depends(database.get_db)):
    return crud.get_chat_history(db, habit.id)

@app.post("/api/chat", response_model=schemas.ChatMessageResponse)
async def send_chat_message(
    chat_req: schemas.ChatRequest,
    habit: database.Habit = Depends(verify_active_habit),
    db: Session = Depends(database.get_db)
):
    # Verify API key is present before attempting Groq request
    if not ai.get_api_key():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Aura Coach is offline. Please configure the GROQ_API_KEY environment variable on the server."
        )

    # 1. Save user's message
    user_msg_schema = schemas.ChatMessageCreate(sender="user", message=chat_req.message)
    crud.create_chat_message(db, user_msg_schema, habit.id)

    # 2. Get past chat history to provide context to the LLM
    history = crud.get_chat_history(db, habit.id, limit=12)

    # 3. Call AI Coach with history context
    try:
        ai_response = await ai.get_coaching_response(habit, history[:-1], chat_req.message, is_sos=chat_req.is_sos)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error communicating with AI service: {str(e)}"
        )

    # 4. Save AI's message
    coach_msg_schema = schemas.ChatMessageCreate(sender="coach", message=ai_response)
    db_coach_msg = crud.create_chat_message(db, coach_msg_schema, habit.id)

    return db_coach_msg

@app.get("/api/nudge", response_model=schemas.NudgeResponse)
async def get_daily_nudge(habit: database.Habit = Depends(verify_active_habit), db: Session = Depends(database.get_db)):
    if not ai.get_api_key():
        return schemas.NudgeResponse(nudge="Aura Coach is offline. Please set GROQ_API_KEY on the server to get daily nudges.")
        
    recent_logs = crud.get_logs(db, habit.id)
    # Take the last 7 logs for context
    nudge_text = await ai.generate_nudge(habit, recent_logs[-7:])
    return schemas.NudgeResponse(nudge=nudge_text)

@app.get("/api/analysis", response_model=schemas.AnalysisResponse)
async def get_weekly_analysis(habit: database.Habit = Depends(verify_active_habit), db: Session = Depends(database.get_db)):
    if not ai.get_api_key():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Aura Coach is offline. Please set GROQ_API_KEY to generate behavioral reviews."
        )
        
    recent_logs = crud.get_logs(db, habit.id)
    analysis_text = await ai.generate_analysis(habit, recent_logs)
    return schemas.AnalysisResponse(analysis=analysis_text)

@app.post("/api/reset")
def reset_application(db: Session = Depends(database.get_db)):
    """Reset all tables in the SQLite database to start fresh."""
    try:
        database.Base.metadata.drop_all(bind=database.engine)
        database.Base.metadata.create_all(bind=database.engine)
        return {"status": "success", "detail": "All application data has been successfully reset."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset application data: {str(e)}"
        )
