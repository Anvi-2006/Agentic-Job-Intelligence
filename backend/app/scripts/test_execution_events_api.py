from uuid import UUID

from fastapi.testclient import TestClient

from backend.app.main import app


APPLICATION_ID = "a9234440-f94f-4650-889f-b4d3c463ffd5"


client = TestClient(app)


print("=== EXECUTION EVENTS API TEST ===")


# 1. GET existing events
response = client.get(
    f"/api/applications/{APPLICATION_ID}/execution/events"
)

assert response.status_code == 200, response.text

events_before = response.json()

print(
    f"[PASS] GET /execution/events -> "
    f"{len(events_before)} existing event(s)"
)


# 2. Record a new event
response = client.post(
    f"/api/applications/{APPLICATION_ID}/execution/events",
    json={
        "event_type": "AUDIT_TEST",
        "step": 1,
        "action": "audit_test",
        "details": "Execution event API test.",
        "success": True,
    },
)

assert response.status_code == 200, response.text

created_event = response.json()

assert created_event["application_id"] if "application_id" in created_event else True
assert created_event["event_type"] == "AUDIT_TEST"
assert created_event["step"] == 1
assert created_event["action"] == "audit_test"
assert created_event["success"] is True

print("[PASS] POST /execution/events -> event created")


# 3. Retrieve events again
response = client.get(
    f"/api/applications/{APPLICATION_ID}/execution/events"
)

assert response.status_code == 200, response.text

events_after = response.json()

assert len(events_after) == len(events_before) + 1

assert any(
    event["event_id"] == created_event["event_id"]
    for event in events_after
)

print("[PASS] GET /execution/events -> created event retrieved")


# 4. Validation: negative step must fail
response = client.post(
    f"/api/applications/{APPLICATION_ID}/execution/events",
    json={
        "event_type": "INVALID_TEST",
        "step": -1,
        "action": "invalid",
        "details": "Negative step should be rejected.",
        "success": False,
    },
)

assert response.status_code == 400

print("[PASS] Negative step rejected")


# 5. Validation: empty event type must fail
response = client.post(
    f"/api/applications/{APPLICATION_ID}/execution/events",
    json={
        "event_type": "",
        "step": 1,
        "action": "invalid",
        "details": "Empty event type should be rejected.",
        "success": False,
    },
)

assert response.status_code == 400

print("[PASS] Empty event type rejected")


# 6. Validation: empty action must fail
response = client.post(
    f"/api/applications/{APPLICATION_ID}/execution/events",
    json={
        "event_type": "INVALID_TEST",
        "step": 1,
        "action": "",
        "details": "Empty action should be rejected.",
        "success": False,
    },
)

assert response.status_code == 400

print("[PASS] Empty action rejected")


print()
print("=== EXECUTION EVENTS API TEST COMPLETE ===")
