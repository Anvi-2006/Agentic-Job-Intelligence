from uuid import UUID

from fastapi.testclient import TestClient

from backend.app.api import application_execution as execution_api
from backend.app.main import app


APPLICATION_ID = "a9234440-f94f-4650-889f-b4d3c463ffd5"


def test_get_execution_endpoint_returns_execution(
    monkeypatch,
):
    def fake_get_application_execution(
        db,
        application_id,
    ):
        assert application_id == UUID(APPLICATION_ID)

        return {
            "execution_id": "11111111-1111-1111-1111-111111111111",
            "application_id": APPLICATION_ID,
            "status": "executing",
            "current_step": 2,
            "current_action": "browser_fields_completed",
            "submission_approved": False,
            "failure_reason": None,
            "started_at": None,
            "completed_at": None,
            "created_at": None,
            "updated_at": None,
        }

    monkeypatch.setattr(
        execution_api,
        "get_application_execution",
        fake_get_application_execution,
    )

    client = TestClient(app)

    response = client.get(
        f"/api/applications/{APPLICATION_ID}/execution",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["application_id"] == APPLICATION_ID
    assert body["status"] == "executing"
    assert body["current_step"] == 2
    assert body["submission_approved"] is False


def test_get_execution_endpoint_returns_404_for_missing_execution(
    monkeypatch,
):
    def fake_get_application_execution(
        db,
        application_id,
    ):
        raise ValueError("Application execution not found.")

    monkeypatch.setattr(
        execution_api,
        "get_application_execution",
        fake_get_application_execution,
    )

    client = TestClient(app)

    response = client.get(
        f"/api/applications/{APPLICATION_ID}/execution",
    )

    assert response.status_code == 404
    assert (
        response.json()["detail"]
        == "Application execution not found."
    )


def test_get_execution_endpoint_rejects_invalid_application_id():
    client = TestClient(app)

    response = client.get(
        "/api/applications/not-a-uuid/execution",
    )

    assert response.status_code == 422
def test_create_execution_endpoint_returns_execution(
    monkeypatch,
):
    def fake_create_application_execution(
        db,
        application_id,
    ):
        assert application_id == UUID(APPLICATION_ID)

        return {
            "execution_id": "11111111-1111-1111-1111-111111111111",
            "application_id": APPLICATION_ID,
            "status": "ready",
            "current_step": 0,
            "current_action": None,
            "submission_approved": False,
            "failure_reason": None,
            "started_at": None,
            "completed_at": None,
            "created_at": None,
            "updated_at": None,
        }

    monkeypatch.setattr(
        execution_api,
        "create_application_execution",
        fake_create_application_execution,
    )

    client = TestClient(app)

    response = client.post(
        f"/api/applications/{APPLICATION_ID}/execution",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["application_id"] == APPLICATION_ID
    assert body["status"] == "ready"
    assert body["current_step"] == 0
    assert body["submission_approved"] is False
def test_start_execution_endpoint_returns_execution(
    monkeypatch,
):
    def fake_start_application_execution(
        db,
        application_id,
    ):
        assert application_id == UUID(APPLICATION_ID)

        return {
            "execution_id": "11111111-1111-1111-1111-111111111111",
            "application_id": APPLICATION_ID,
            "status": "executing",
            "current_step": 0,
            "current_action": "execution_started",
            "submission_approved": False,
            "failure_reason": None,
            "started_at": None,
            "completed_at": None,
            "created_at": None,
            "updated_at": None,
        }

    monkeypatch.setattr(
        execution_api,
        "start_application_execution",
        fake_start_application_execution,
    )

    client = TestClient(app)

    response = client.post(
        f"/api/applications/{APPLICATION_ID}/execution/start",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["application_id"] == APPLICATION_ID
    assert body["status"] == "executing"
    assert body["current_action"] == "execution_started"
    assert body["submission_approved"] is False
def test_request_submission_approval_endpoint_returns_needs_human(
    monkeypatch,
):
    def fake_request_submission_approval(
        db,
        application_id,
    ):
        assert application_id == UUID(APPLICATION_ID)

        return {
            "execution_id": "11111111-1111-1111-1111-111111111111",
            "application_id": APPLICATION_ID,
            "status": "needs_human",
            "current_step": 0,
            "current_action": "submission_approval_required",
            "submission_approved": False,
            "failure_reason": None,
            "started_at": None,
            "completed_at": None,
            "created_at": None,
            "updated_at": None,
        }

    monkeypatch.setattr(
        execution_api,
        "request_submission_approval",
        fake_request_submission_approval,
    )

    client = TestClient(app)

    response = client.post(
        f"/api/applications/{APPLICATION_ID}/execution/request-submission-approval",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["application_id"] == APPLICATION_ID
    assert body["status"] == "needs_human"
    assert body["current_action"] == "submission_approval_required"
    assert body["submission_approved"] is False
def test_approve_submission_endpoint_returns_executing(
    monkeypatch,
):
    def fake_approve_application_submission(
        db,
        application_id,
    ):
        assert application_id == UUID(APPLICATION_ID)

        return {
            "execution_id": "11111111-1111-1111-1111-111111111111",
            "application_id": APPLICATION_ID,
            "status": "executing",
            "current_step": 0,
            "current_action": "submission_approved",
            "submission_approved": True,
            "failure_reason": None,
            "started_at": None,
            "completed_at": None,
            "created_at": None,
            "updated_at": None,
        }

    monkeypatch.setattr(
        execution_api,
        "approve_application_submission",
        fake_approve_application_submission,
    )

    client = TestClient(app)

    response = client.post(
        f"/api/applications/{APPLICATION_ID}/execution/approve-submission",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["application_id"] == APPLICATION_ID
    assert body["status"] == "executing"
    assert body["current_action"] == "submission_approved"
    assert body["submission_approved"] is True
def test_mark_submitted_endpoint_returns_submitted(
    monkeypatch,
):
    def fake_mark_execution_submitted(
        db,
        application_id,
    ):
        assert application_id == UUID(APPLICATION_ID)

        return {
            "execution_id": "11111111-1111-1111-1111-111111111111",
            "application_id": APPLICATION_ID,
            "status": "submitted",
            "current_step": 1,
            "current_action": "application_submitted",
            "submission_approved": True,
            "failure_reason": None,
            "started_at": None,
            "completed_at": None,
            "created_at": None,
            "updated_at": None,
        }

    monkeypatch.setattr(
        execution_api,
        "mark_execution_submitted",
        fake_mark_execution_submitted,
    )

    client = TestClient(app)

    response = client.post(
        f"/api/applications/{APPLICATION_ID}/execution/submitted",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["application_id"] == APPLICATION_ID
    assert body["status"] == "submitted"
    assert body["current_action"] == "application_submitted"
    assert body["submission_approved"] is True
def test_needs_human_endpoint_returns_needs_human(
    monkeypatch,
):
    def fake_mark_execution_needs_human(
        db,
        application_id,
        current_action,
    ):
        assert application_id == UUID(APPLICATION_ID)
        assert current_action == "human_input_required"

        return {
            "execution_id": "11111111-1111-1111-1111-111111111111",
            "application_id": APPLICATION_ID,
            "status": "needs_human",
            "current_step": 1,
            "current_action": "human_input_required",
            "submission_approved": False,
            "failure_reason": None,
            "started_at": None,
            "completed_at": None,
            "created_at": None,
            "updated_at": None,
        }

    monkeypatch.setattr(
        execution_api,
        "mark_execution_needs_human",
        fake_mark_execution_needs_human,
    )

    client = TestClient(app)

    response = client.post(
        f"/api/applications/{APPLICATION_ID}/execution/needs-human",
        json={"current_action": "human_input_required"},
    )

    assert response.status_code == 200

    body = response.json()

    assert body["application_id"] == APPLICATION_ID
    assert body["status"] == "needs_human"
    assert body["current_action"] == "human_input_required"
    assert body["submission_approved"] is False
def test_failed_endpoint_returns_failed(
    monkeypatch,
):
    def fake_mark_execution_failed(
        db,
        application_id,
        failure_reason,
    ):
        assert application_id == UUID(APPLICATION_ID)
        assert failure_reason == "Browser execution failed."

        return {
            "execution_id": "11111111-1111-1111-1111-111111111111",
            "application_id": APPLICATION_ID,
            "status": "failed",
            "current_step": 1,
            "current_action": "execution_failed",
            "submission_approved": False,
            "failure_reason": "Browser execution failed.",
            "started_at": None,
            "completed_at": None,
            "created_at": None,
            "updated_at": None,
        }

    monkeypatch.setattr(
        execution_api,
        "mark_execution_failed",
        fake_mark_execution_failed,
    )

    client = TestClient(app)

    response = client.post(
        f"/api/applications/{APPLICATION_ID}/execution/failed",
        json={"failure_reason": "Browser execution failed."},
    )

    assert response.status_code == 200

    body = response.json()

    assert body["application_id"] == APPLICATION_ID
    assert body["status"] == "failed"
    assert body["failure_reason"] == "Browser execution failed."
    assert body["submission_approved"] is False
def test_resume_execution_endpoint_returns_executing(
    monkeypatch,
):
    def fake_resume_application_execution(
        db,
        application_id,
    ):
        assert application_id == UUID(APPLICATION_ID)

        return {
            "execution_id": "11111111-1111-1111-1111-111111111111",
            "application_id": APPLICATION_ID,
            "status": "executing",
            "current_step": 1,
            "current_action": "execution_resumed",
            "submission_approved": False,
            "failure_reason": None,
            "started_at": None,
            "completed_at": None,
            "created_at": None,
            "updated_at": None,
        }

    monkeypatch.setattr(
        execution_api,
        "resume_application_execution",
        fake_resume_application_execution,
    )

    client = TestClient(app)

    response = client.post(
        f"/api/applications/{APPLICATION_ID}/execution/resume",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["application_id"] == APPLICATION_ID
    assert body["status"] == "executing"
    assert body["current_action"] == "execution_resumed"
    assert body["submission_approved"] is False
def test_retry_failed_execution_endpoint_returns_ready(
    monkeypatch,
):
    def fake_retry_failed_execution(
        db,
        application_id,
    ):
        assert application_id == UUID(APPLICATION_ID)

        return {
            "execution_id": "11111111-1111-1111-1111-111111111111",
            "application_id": APPLICATION_ID,
            "status": "ready",
            "current_step": 0,
            "current_action": "retry_ready",
            "submission_approved": False,
            "failure_reason": None,
            "started_at": None,
            "completed_at": None,
            "created_at": None,
            "updated_at": None,
        }

    monkeypatch.setattr(
        execution_api,
        "retry_failed_execution",
        fake_retry_failed_execution,
    )

    client = TestClient(app)

    response = client.post(
        f"/api/applications/{APPLICATION_ID}/execution/retry",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["application_id"] == APPLICATION_ID
    assert body["status"] == "ready"
    assert body["current_step"] == 0
    assert body["submission_approved"] is False
    assert body["failure_reason"] is None
def test_update_execution_step_endpoint_returns_updated_execution(
    monkeypatch,
):
    def fake_update_execution_step(
        db,
        application_id,
        current_step,
        current_action,
    ):
        assert application_id == UUID(APPLICATION_ID)
        assert current_step == 2
        assert current_action == "browser_fields_completed"

        return {
            "execution_id": "11111111-1111-1111-1111-111111111111",
            "application_id": APPLICATION_ID,
            "status": "executing",
            "current_step": 2,
            "current_action": "browser_fields_completed",
            "submission_approved": False,
            "failure_reason": None,
            "started_at": None,
            "completed_at": None,
            "created_at": None,
            "updated_at": None,
        }

    monkeypatch.setattr(
        execution_api,
        "update_execution_step",
        fake_update_execution_step,
    )

    client = TestClient(app)

    response = client.post(
        f"/api/applications/{APPLICATION_ID}/execution/step",
        json={
            "current_step": 2,
            "current_action": "browser_fields_completed",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["application_id"] == APPLICATION_ID
    assert body["status"] == "executing"
    assert body["current_step"] == 2
    assert body["current_action"] == "browser_fields_completed"
def test_browser_execution_endpoint_returns_execution(
    monkeypatch,
):
    def fake_execute_application_browser_step(
        application_id,
        application_url,
        headless,
    ):
        assert application_id == UUID(APPLICATION_ID)
        assert application_url == "https://example.com/apply"
        assert headless is True

        return {
            "execution_id": "11111111-1111-1111-1111-111111111111",
            "application_id": APPLICATION_ID,
            "status": "executing",
            "current_step": 2,
            "current_action": "browser_fields_completed",
            "submission_approved": False,
            "failure_reason": None,
            "started_at": None,
            "completed_at": None,
            "created_at": None,
            "updated_at": None,
        }

    monkeypatch.setattr(
        execution_api,
        "execute_application_browser_step",
        fake_execute_application_browser_step,
    )

    client = TestClient(app)

    response = client.post(
        f"/api/applications/{APPLICATION_ID}/execution/browser",
        json={
            "application_url": "https://example.com/apply",
            "headless": True,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["application_id"] == APPLICATION_ID
    assert body["status"] == "executing"
    assert body["current_step"] == 2
    assert body["current_action"] == "browser_fields_completed"
    assert body["submission_approved"] is False


def test_browser_execution_endpoint_returns_needs_human(
    monkeypatch,
):
    def fake_execute_application_browser_step(
        application_id,
        application_url,
        headless,
    ):
        assert application_id == UUID(APPLICATION_ID)
        assert application_url == "https://example.com/apply"
        assert headless is True

        return {
            "execution_id": "11111111-1111-1111-1111-111111111111",
            "application_id": APPLICATION_ID,
            "status": "needs_human",
            "current_step": 2,
            "current_action": "browser_human_intervention",
            "submission_approved": False,
            "failure_reason": None,
            "started_at": None,
            "completed_at": None,
            "created_at": None,
            "updated_at": None,
        }

    monkeypatch.setattr(
        execution_api,
        "execute_application_browser_step",
        fake_execute_application_browser_step,
    )

    client = TestClient(app)

    response = client.post(
        f"/api/applications/{APPLICATION_ID}/execution/browser",
        json={
            "application_url": "https://example.com/apply",
            "headless": True,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["application_id"] == APPLICATION_ID
    assert body["status"] == "needs_human"
    assert body["current_step"] == 2
    assert body["current_action"] == "browser_human_intervention"
    assert body["submission_approved"] is False