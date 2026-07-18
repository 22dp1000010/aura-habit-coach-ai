import httpx
import sys

BASE_URL = "http://localhost:8000/api"

def run_verification():
    print("=== Start Stateless E2E API Verification ===")
    
    # 1. Health check
    try:
        res = httpx.get(f"{BASE_URL}/health")
        print(f"Health Check: {res.status_code} - {res.json()}")
    except Exception as e:
        print(f"Failed to connect to backend server: {e}")
        sys.exit(1)

    # 2. Check Daily Nudge POST Request
    nudge_payload = {
        "habit": {
            "name": "Excessive Screen Time",
            "description": "Doomscrolling late at night",
            "triggers": "Boredom",
            "motivation": "Sleep focus",
            "target_reduction": "30 mins limit"
        },
        "recent_logs": [
            {
                "date": "2026-07-18",
                "metric_value": 45.0,
                "craving_level": 7,
                "slip_up": True,
                "notes": "Stress scrolling"
            }
        ]
    }
    
    res = httpx.post(f"{BASE_URL}/nudge", json=nudge_payload)
    print(f"Nudge Fetch: {res.status_code} - {res.json()}")
    assert res.status_code == 200

    # 3. Check invalid input validation constraints (craving = 15, should return 422)
    bad_payload = {
        "habit": {
            "name": "Excessive Screen Time"
        },
        "recent_logs": [
            {
                "date": "2026-07-18",
                "metric_value": 45.0,
                "craving_level": 15,  # Out of range
                "slip_up": True
            }
        ]
    }
    res = httpx.post(f"{BASE_URL}/nudge", json=bad_payload)
    print(f"Bad input rejection: {res.status_code} (expect 422)")
    assert res.status_code == 422

    print("=== Stateless E2E API Verification Complete: SUCCESS ===")

if __name__ == "__main__":
    run_verification()
