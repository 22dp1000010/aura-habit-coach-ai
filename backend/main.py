import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone

from . import schemas, ai

@asynccontextmanager
async def lifespan(app: FastAPI):
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

app = FastAPI(
    title="Aura: AI Habit Coach API (Stateless)",
    description="Stateless Backend API for CBT-based cognitive coaching powered by Groq",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoints
@app.get("/api/health")
async def health_check():
    api_key = ai.get_api_key()
    ai_status = "configured" if api_key else "missing"
    return {
        "status": "ok",
        "database": "none",
        "ai_service": ai_status
    }

@app.post("/api/chat", response_model=schemas.ChatMessageResponse)
async def send_chat_message(
    chat_req: schemas.ChatRequest
):
    if not ai.get_api_key():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Aura Coach is offline. Please configure the GROQ_API_KEY environment variable on the server."
        )

    try:
        # Call AI Coach with history context
        ai_response = await ai.get_coaching_response(
            chat_req.habit, 
            chat_req.history, 
            chat_req.message, 
            is_sos=chat_req.is_sos
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error communicating with AI service: {str(e)}"
        )

    return schemas.ChatMessageResponse(
        sender="coach",
        message=ai_response,
        timestamp=datetime.now(timezone.utc).isoformat()
    )

@app.post("/api/nudge", response_model=schemas.NudgeResponse)
async def get_daily_nudge(nudge_req: schemas.NudgeRequest):
    if not ai.get_api_key():
        return schemas.NudgeResponse(nudge="Aura Coach is offline. Please set GROQ_API_KEY on Vercel to get daily nudges.")
        
    # Take the last 7 logs for context
    nudge_text = await ai.generate_nudge(nudge_req.habit, nudge_req.recent_logs[-7:])
    return schemas.NudgeResponse(nudge=nudge_text)

@app.post("/api/analysis", response_model=schemas.AnalysisResponse)
async def get_weekly_analysis(analysis_req: schemas.AnalysisRequest):
    if not ai.get_api_key():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Aura Coach is offline. Please set GROQ_API_KEY to generate behavioral reviews."
        )
        
    analysis_text = await ai.generate_analysis(analysis_req.habit, analysis_req.recent_logs)
    return schemas.AnalysisResponse(analysis=analysis_text)
