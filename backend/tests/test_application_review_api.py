from uuid import UUID

from fastapi.testclient import TestClient

from backend.app.api import application_review as application_review_api
from backend.app.main import app


CANDIDATE_ID = "332b3f24-eefc-4d05-99d5-56798d24a50c"
JOB_ID = "5720e13e-bbc2-4ee4-8cbd-25497b83eb2e"
APPLICATION_ID = "a9234440-f94f-4650-889f-b4d3c463ffd5"


def test_review_application_endpoint_returns_approved_application(
    monkeypatch,
):
    def fake_review_application(
        db,
        candidate_id,
        job_id,
        decision,
        reviewer_note,
    ):
        assert candidate_id == UUID(CANDIDATE_ID)
        assert job_id == UUID(JOB_ID)
        assert decision == "APPROVED"
        assert reviewer_note == "Approved for submission."

        return {
            "application_id": APPLICATION_ID,
            "candidate_id": CANDIDATE_ID,
            "job_id": JOB_ID,
            "company": "Demo Company",
            "job_title": "Software Engineer",
            "fit_score": 90.0,
            "recommendation": "APPLY",
            "status": "approved",
            "reviewer_note": reviewer_note,
        }

    monkeypatch.setattr(
        application_review_api,
        "review_application",
        fake_review_application,
    )

    client = TestClient(app)

    response = client.post(
        f"/api/applications/{CANDIDATE_ID}/{JOB_ID}/review",
        json={
            "decision": "APPROVED",
            "reviewer_note": "Approved for submission.",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["application_id"] == APPLICATION_ID
    assert body["candidate_id"] == CANDIDATE_ID
    assert body["job_id"] == JOB_ID
    assert body["status"] == "approved"
    assert body["reviewer_note"] == "Approved for submission."


def test_review_application_endpoint_returns_400_for_invalid_decision(
    monkeypatch,
):
    def fake_review_application(
        db,
        candidate_id,
        job_id,
        decision,
        reviewer_note,
    ):
        raise ValueError(
            "Invalid decision. Use APPROVED, EDIT_REQUIRED, or REJECTED."
        )

    monkeypatch.setattr(
        application_review_api,
        "review_application",
        fake_review_application,
    )

    client = TestClient(app)

    response = client.post(
        f"/api/applications/{CANDIDATE_ID}/{JOB_ID}/review",
        json={
            "decision": "INVALID",
        },
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Invalid decision. Use APPROVED, EDIT_REQUIRED, or REJECTED."
    )


def test_get_application_review_endpoint_returns_details(
    monkeypatch,
):
    def fake_get_application_review(db, application_id):
        assert application_id == UUID(APPLICATION_ID)

        return {
            "application_id": APPLICATION_ID,
            "candidate_id": CANDIDATE_ID,
            "job_id": JOB_ID,
            "company": "Demo Company",
            "job_title": "Software Engineer",
            "fit_score": 90.0,
            "recommendation": "APPLY",
            "status": "pending_review",
            "reviewer_note": None,
            "readiness_score": 85.0,
            "tailored_summary": "A tailored summary.",
            "cover_letter": "A cover letter.",
            "key_strengths": ["Python", "FastAPI"],
            "missing_requirements": [],
            "application_questions": [],
            "evidence_used": ["resume"],
            "unsupported_claims": [],
            "is_valid": True,
        }

    monkeypatch.setattr(
        application_review_api,
        "get_application_review",
        fake_get_application_review,
    )

    client = TestClient(app)

    response = client.get(
        f"/api/applications/review/{APPLICATION_ID}",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["application_id"] == APPLICATION_ID
    assert body["fit_score"] == 90.0
    assert body["readiness_score"] == 85.0
    assert body["is_valid"] is True


def test_get_application_review_endpoint_returns_404_for_missing_application(
    monkeypatch,
):
    def fake_get_application_review(db, application_id):
        raise ValueError("Application not found.")

    monkeypatch.setattr(
        application_review_api,
        "get_application_review",
        fake_get_application_review,
    )

    client = TestClient(app)

    response = client.get(
        f"/api/applications/review/{APPLICATION_ID}",
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found."


def test_review_application_endpoint_rejects_invalid_candidate_id():
    client = TestClient(app)

    response = client.post(
        "/api/applications/not-a-uuid/" + JOB_ID + "/review",
        json={"decision": "APPROVED"},
    )

    assert response.status_code == 422