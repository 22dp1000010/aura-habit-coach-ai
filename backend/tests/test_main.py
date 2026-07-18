import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import os

# We must set a database url env variable for testing to use an in-memory or distinct test SQLite database
os.environ["DATABASE_URL"] = "sqlite:///./test_aura.db"
os.environ["GROQ_API_KEY"] = "gsk_testkeyvalue"

from backend.main import app
from backend.database import Base, engine, SessionLocal
from backend import ai

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    # Setup: Create tables
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Clear existing tables to ensure clean runs
        db.execute(Base.metadata.tables["logs"].delete())
        db.execute(Base.metadata.tables["chat_messages"].delete())
        db.execute(Base.metadata.tables["habits"].delete())
        db.commit()
    finally:
        db.close()
    yield
    # Teardown: Clean up
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_aura.db"):
        try:
            os.remove("./test_aura.db")
        except PermissionError:
            pass

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "database" in data
    assert data["ai_service"] == "configured"

def test_get_habit_not_found():
    response = client.get("/api/habit")
    assert response.status_code == 404
    assert "detail" in response.json()

def test_create_and_get_habit():
    # Create habit
    payload = {
        "name": "Excessive Screen Time",
        "description": "Doomscrolling social media applications late at night",
        "triggers": "Boredom, lying in bed, notifications",
        "motivation": "Better sleep and morning focus",
        "target_reduction": "Limit to 30 minutes daily before bed"
    }
    response = client.post("/api/habit", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] is not None
    assert data["name"] == payload["name"]
    assert data["description"] == payload["description"]
    
    # Get habit
    response = client.get("/api/habit")
    assert response.status_code == 200
    assert response.json()["name"] == payload["name"]

def test_input_validation():
    # Attempting to create an invalid habit (empty name)
    payload = {
        "name": "",
        "description": "Short desc"
    }
    response = client.post("/api/habit", json=payload)
    assert response.status_code == 422 # Unprocessable Entity

def test_logs_workflow():
    # Setup a habit first
    habit_payload = {
        "name": "Doomscrolling",
        "description": "Scrolling social media",
        "triggers": "Boredom",
        "motivation": "Productivity",
        "target_reduction": "30 mins"
    }
    client.post("/api/habit", json=habit_payload)
    
    # Send daily log
    log_payload = {
        "date": "2026-07-18",
        "metric_value": 45.5,
        "craving_level": 7,
        "slip_up": True,
        "notes": "Felt stressed and scrolled for 45 minutes after work."
    }
    response = client.post("/api/logs", json=log_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] is not None
    assert data["metric_value"] == 45.5
    assert data["craving_level"] == 7
    assert data["slip_up"] is True
    
    # Send another log with validation error (craving_level out of bounds)
    bad_log = {
        "date": "2026-07-19",
        "metric_value": 15,
        "craving_level": 11, # Max is 10
        "slip_up": False
    }
    response = client.post("/api/logs", json=bad_log)
    assert response.status_code == 422

    # Get logs list
    response = client.get("/api/logs")
    assert response.status_code == 200
    logs = response.json()
    assert len(logs) == 1
    assert logs[0]["date"] == "2026-07-18"

@patch("backend.ai.fetch_groq_completion", new_callable=AsyncMock)
def test_chat_workflow(mock_completion):
    # Setup mock
    mock_completion.return_value = "Aura response: Keep taking deep breaths. You are in control."

    # Setup habit
    habit_payload = {"name": "Smoking", "description": "Smoking cigarettes", "triggers": "Stress", "motivation": "Health", "target_reduction": "Zero"}
    client.post("/api/habit", json=habit_payload)

    # Send normal chat message
    chat_payload = {
        "message": "I'm having a craving right now.",
        "is_sos": False
    }
    response = client.post("/api/chat", json=chat_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["sender"] == "coach"
    assert data["message"] == "Aura response: Keep taking deep breaths. You are in control."

    # Get chat history
    response = client.get("/api/chat/history")
    assert response.status_code == 200
    history = response.json()
    # Should have two messages: User's message and Aura's reply
    assert len(history) == 2
    assert history[0]["sender"] == "user"
    assert history[0]["message"] == "I'm having a craving right now."
    assert history[1]["sender"] == "coach"

@patch("backend.ai.fetch_groq_completion", new_callable=AsyncMock)
def test_nudge_workflow(mock_completion):
    mock_completion.return_value = "Remember: you are stronger than your urges today."
    
    # Setup habit
    habit_payload = {"name": "Smoking", "description": "Smoking cigarettes", "triggers": "Stress", "motivation": "Health", "target_reduction": "Zero"}
    client.post("/api/habit", json=habit_payload)

    response = client.get("/api/nudge")
    assert response.status_code == 200
    assert response.json()["nudge"] == "Remember: you are stronger than your urges today."
