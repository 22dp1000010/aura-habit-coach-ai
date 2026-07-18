import httpx
import sys

BASE_URL = "http://localhost:8000/api"

def run_verification():
    print("=== Start E2E API Verification ===")
    
    # 1. Health check
    try:
        res = httpx.get(f"{BASE_URL}/health")
        print(f"Health Check: {res.status_code} - {res.json()}")
    except Exception as e:
        print(f"Failed to connect to backend server: {e}")
        sys.exit(1)

    # 2. Reset database to start clean
    res = httpx.post(f"{BASE_URL}/reset")
    print(f"Reset Database: {res.status_code} - {res.json()}")

    # 3. Verify get habit returns 404 (clean state)
    res = httpx.get(f"{BASE_URL}/habit")
    print(f"Get Habit (should be 404): {res.status_code}")
    assert res.status_code == 404

    # 4. Setup Habit Onboarding
    habit_payload = {
        "name": "Excessive Screen Time",
        "description": "Doomscrolling on social media late at night",
        "triggers": "Boredom, bed, notifications",
        "motivation": "Improve deep sleep and morning focus",
        "target_reduction": "Limit to 30 minutes daily before bed"
    }
    res = httpx.post(f"{BASE_URL}/habit", json=habit_payload)
    print(f"Setup Habit: {res.status_code} - {res.json()}")
    assert res.status_code == 200
    habit_id = res.json()["id"]

    # 5. Fetch Habit
    res = httpx.get(f"{BASE_URL}/habit")
    print(f"Fetch Habit: {res.status_code} - {res.json()}")
    assert res.status_code == 200
    assert res.json()["name"] == "Excessive Screen Time"

    # 6. Post Daily Log with a Slip-up
    log_payload = {
        "date": "2026-07-18",
        "metric_value": 45.0,
        "craving_level": 7,
        "slip_up": True,
        "notes": "Felt stressed after work and doomscrolled."
    }
    res = httpx.post(f"{BASE_URL}/logs", json=log_payload)
    print(f"Log Daily Check-in: {res.status_code} - {res.json()}")
    assert res.status_code == 200

    # 7. Post Daily Log with a Success (Different date)
    success_log_payload = {
        "date": "2026-07-19",
        "metric_value": 15.0,
        "craving_level": 3,
        "slip_up": False,
        "notes": "Surfed the urge and read a book instead."
    }
    res = httpx.post(f"{BASE_URL}/logs", json=success_log_payload)
    print(f"Log Daily Success Check-in: {res.status_code} - {res.json()}")
    assert res.status_code == 200

    # 8. Fetch Logs History
    res = httpx.get(f"{BASE_URL}/logs")
    print(f"Fetch Logs History: {res.status_code} - {len(res.json())} logs found")
    assert res.status_code == 200
    assert len(res.json()) == 2

    # 9. Verify invalid log input validation constraint (craving = 15, should fail 422)
    bad_log = {
        "date": "2026-07-20",
        "metric_value": 10.0,
        "craving_level": 15,  # Invalid level
        "slip_up": False,
        "notes": "Invalid log"
    }
    res = httpx.post(f"{BASE_URL}/logs", json=bad_log)
    print(f"Log Bad Check-in validation: {res.status_code} (expect 422)")
    assert res.status_code == 422

    print("=== E2E API Verification Complete: SUCCESS ===")

if __name__ == "__main__":
    run_verification()
