import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import os

os.environ["GROQ_API_KEY"] = "gsk_testkeyvalue"

from backend.main import app
from backend import ai

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "none"
    assert data["ai_service"] == "configured"

@patch("backend.ai.fetch_groq_completion", new_callable=AsyncMock)
def test_chat_stateless(mock_completion):
    mock_completion.return_value = "Aura Response: Try counting backwards from 100."
    
    payload = {
        "habit": {
            "name": "Excessive Screen Time",
            "description": "Doomscrolling late at night",
            "triggers": "Boredom",
            "motivation": "Sleep quality",
            "target_reduction": "30 mins limit"
        },
        "history": [
            {"sender": "user", "message": "Hi"},
            {"sender": "coach", "message": "Hello! How can I support you?"}
        ],
        "message": "I feel like scrolling.",
        "is_sos": False
    }
    
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["sender"] == "coach"
    assert data["message"] == "Aura Response: Try counting backwards from 100."
    assert "timestamp" in data

@patch("backend.ai.fetch_groq_completion", new_callable=AsyncMock)
def test_nudge_stateless(mock_completion):
    mock_completion.return_value = "Keep going! You're making progress."
    
    payload = {
        "habit": {
            "name": "Nail Biting",
            "description": "Nail biting during stress",
            "triggers": "Work meetings",
            "motivation": "Sore fingers",
            "target_reduction": "Zero instances"
        },
        "recent_logs": [
            {
                "date": "2026-07-18",
                "metric_value": 0,
                "craving_level": 4,
                "slip_up": False,
                "notes": "Kept hands busy."
            }
        ]
    }
    
    response = client.post("/api/nudge", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["nudge"] == "Keep going! You're making progress."

@patch("backend.ai.fetch_groq_completion", new_callable=AsyncMock)
def test_analysis_stateless(mock_completion):
    mock_completion.return_value = "Weekly behavioral review complete."
    
    payload = {
        "habit": {
            "name": "Sugar Intake",
            "description": "Sweets after dinner",
            "triggers": "TV time",
            "motivation": "Dental health",
            "target_reduction": "Limit to weekends"
        },
        "recent_logs": [
            {
                "date": "2026-07-18",
                "metric_value": 2,
                "craving_level": 8,
                "slip_up": True,
                "notes": "Ate cookies during movie."
            }
        ]
    }
    
    response = client.post("/api/analysis", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["analysis"] == "Weekly behavioral review complete."

def test_validation_constraints():
    # Sending a daily log payload with an out of bounds craving level (15, valid is 1-10)
    payload = {
        "habit": {
            "name": "Nail Biting"
        },
        "recent_logs": [
            {
                "date": "2026-07-18",
                "metric_value": 0,
                "craving_level": 15,  # Out of range (max 10)
                "slip_up": False
            }
        ]
    }
    
    response = client.post("/api/nudge", json=payload)
    assert response.status_code == 422  # Unprocessable Entity
