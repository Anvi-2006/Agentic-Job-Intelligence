import uuid
from uuid import UUID

from fastapi.testclient import TestClient

from backend.app.core.database import SessionLocal
from backend.app.main import app
from backend.app.models.application import Application
from backend.app.models.application_execution import ApplicationExecution
from backend.app.models.application_package import ApplicationPackage
from backend.app.models.execution_event import ExecutionEvent
from backend.app.models.human_input_request import HumanInputRequest


SOURCE_APPLICATION_ID = UUID(
    "a9234440-f94f-4650-889f-b4d3c463ffd5"
)

client = TestClient(app)


def create_test_application():
    db = SessionLocal()

    try:
        source_application = db.get(
            Application,
            SOURCE_APPLICATION_ID,
        )

        if source_application is None:
            raise RuntimeError(
                "Source application not found."
            )

        if source_application.status != "approved":
            raise RuntimeError(
                f"Source application must be approved. "
                f"Current status: {source_application.status}"
            )

        source_package = (
            db.query(ApplicationPackage)
            .filter(
                ApplicationPackage.application_id
                == SOURCE_APPLICATION_ID
            )
            .first()
        )

        if source_package is None:
            raise RuntimeError(
                "Source application package not found."
            )

        test_application = Application(
            id=uuid.uuid4(),
            candidate_id=source_application.candidate_id,
            job_id=source_application.job_id,
            fit_score=source_application.fit_score,
            recommendation=source_application.recommendation,
            status="approved",
            reviewer_note="Temporary execution API test.",
        )

        db.add(test_application)
        db.flush()

        test_package = ApplicationPackage(
            id=uuid.uuid4(),
            application_id=test_application.id,
            readiness_score=source_package.readiness_score,
            tailored_summary=source_package.tailored_summary,
            cover_letter=source_package.cover_letter,
            key_strengths=source_package.key_strengths,
            missing_requirements=source_package.missing_requirements,
            application_questions=source_package.application_questions,
            evidence_used=source_package.evidence_used,
            unsupported_claims=source_package.unsupported_claims,
            is_valid=source_package.is_valid,
        )

        db.add(test_package)
        db.commit()

        return test_application.id

    finally:
        db.close()


def cleanup_test_application(application_id):
    db = SessionLocal()

    try:
        executions = (
            db.query(ApplicationExecution)
            .filter(
                ApplicationExecution.application_id
                == application_id
            )
            .all()
        )

        execution_ids = [
            execution.id
            for execution in executions
        ]

        if execution_ids:
            db.query(HumanInputRequest).filter(
                HumanInputRequest.execution_id.in_(
                    execution_ids
                )
            ).delete(
                synchronize_session=False
            )

            db.query(ExecutionEvent).filter(
                ExecutionEvent.execution_id.in_(
                    execution_ids
                )
            ).delete(
                synchronize_session=False
            )

            db.query(ApplicationExecution).filter(
                ApplicationExecution.id.in_(
                    execution_ids
                )
            ).delete(
                synchronize_session=False
            )

        db.query(ApplicationPackage).filter(
            ApplicationPackage.application_id
            == application_id
        ).delete(
            synchronize_session=False
        )

        db.query(Application).filter(
            Application.id == application_id
        ).delete(
            synchronize_session=False
        )

        db.commit()

    finally:
        db.close()


def get_execution(application_id):
    db = SessionLocal()

    try:
        return (
            db.query(ApplicationExecution)
            .filter(
                ApplicationExecution.application_id
                == application_id
            )
            .first()
        )

    finally:
        db.close()


def main():
    application_id = None

    try:
        application_id = create_test_application()

        print(
            "\n=== APPLICATION EXECUTION API TEST ===\n"
        )

        print(
            "[PASS] Temporary approved application created"
        )

        # -----------------------------------------------------
        # 1. Create execution
        # -----------------------------------------------------

        response = client.post(
            f"/api/applications/{application_id}/execution"
        )

        assert response.status_code == 200, response.text

        data = response.json()

        assert data["status"] == "ready"
        assert data["submission_approved"] is False

        print("[PASS] POST /execution -> ready")

        # -----------------------------------------------------
        # 2. Start execution
        # -----------------------------------------------------

        response = client.post(
            f"/api/applications/{application_id}/execution/start"
        )

        assert response.status_code == 200, response.text

        data = response.json()

        assert data["status"] == "executing"
        assert data["submission_approved"] is False

        print("[PASS] POST /execution/start -> executing")

        # -----------------------------------------------------
        # 3. Update execution step
        # -----------------------------------------------------

        response = client.post(
            f"/api/applications/{application_id}/execution/step",
            json={
                "current_step": 1,
                "current_action": "open_application_page",
            },
        )

        assert response.status_code == 200, response.text

        data = response.json()

        assert data["current_step"] == 1
        assert (
            data["current_action"]
            == "open_application_page"
        )

        print("[PASS] POST /execution/step")

        # -----------------------------------------------------
        # 4. Request human intervention
        # -----------------------------------------------------

        response = client.post(
            f"/api/applications/{application_id}/execution/needs-human",
            json={
                "current_action": "captcha_detected",
            },
        )

        assert response.status_code == 200, response.text

        data = response.json()

        assert data["status"] == "needs_human"
        assert (
            data["current_action"]
            == "captcha_detected"
        )

        print("[PASS] POST /execution/needs-human")

        # -----------------------------------------------------
        # 5. Resume execution
        # -----------------------------------------------------

        response = client.post(
            f"/api/applications/{application_id}/execution/resume"
        )

        assert response.status_code == 200, response.text

        data = response.json()

        assert data["status"] == "executing"
        assert data["current_action"] == "resuming"

        print(
            "[PASS] POST /execution/resume -> executing"
        )

        # -----------------------------------------------------
        # 6. Fail execution
        # -----------------------------------------------------

        response = client.post(
            f"/api/applications/{application_id}/execution/failed",
            json={
                "failure_reason":
                    "Application portal temporarily unavailable.",
            },
        )

        assert response.status_code == 200, response.text

        data = response.json()

        assert data["status"] == "failed"
        assert (
            data["failure_reason"]
            == "Application portal temporarily unavailable."
        )
        assert data["completed_at"] is not None

        print("[PASS] POST /execution/failed")

        # -----------------------------------------------------
        # 7. Retry failed execution
        # -----------------------------------------------------

        response = client.post(
            f"/api/applications/{application_id}/execution/retry"
        )

        assert response.status_code == 200, response.text

        data = response.json()

        assert data["status"] == "ready"
        assert data["failure_reason"] is None
        assert data["completed_at"] is None
        assert data["submission_approved"] is False

        print("[PASS] POST /execution/retry -> ready")

        # -----------------------------------------------------
        # 8. Start second execution attempt
        # -----------------------------------------------------

        response = client.post(
            f"/api/applications/{application_id}/execution/start"
        )

        assert response.status_code == 200, response.text

        data = response.json()

        assert data["status"] == "executing"
        assert data["submission_approved"] is False

        print("[PASS] retry ready -> executing")

        # -----------------------------------------------------
        # 9. Request submission approval
        # -----------------------------------------------------

        response = client.post(
            f"/api/applications/{application_id}/execution/request-submission-approval"
        )

        assert response.status_code == 200, response.text

        data = response.json()

        assert data["status"] == "needs_human"
        assert (
            data["current_action"]
            == "submission_approval_required"
        )
        assert data["submission_approved"] is False

        print(
            "[PASS] POST /execution/request-submission-approval"
        )

        # -----------------------------------------------------
        # 10. Submission must remain blocked before approval
        # -----------------------------------------------------

        response = client.post(
            f"/api/applications/{application_id}/execution/submitted"
        )

        assert response.status_code == 400

        print(
            "[PASS] submission blocked before human approval"
        )

        # -----------------------------------------------------
        # 11. Explicitly approve submission
        # -----------------------------------------------------

        response = client.post(
            f"/api/applications/{application_id}/execution/approve-submission"
        )

        assert response.status_code == 200, response.text

        data = response.json()

        assert data["status"] == "executing"
        assert (
            data["current_action"]
            == "submission_approved"
        )
        assert data["submission_approved"] is True

        print(
            "[PASS] POST /execution/approve-submission"
        )

        # -----------------------------------------------------
        # 12. Submit application
        # -----------------------------------------------------

        response = client.post(
            f"/api/applications/{application_id}/execution/submitted"
        )

        assert response.status_code == 200, response.text

        data = response.json()

        assert data["status"] == "submitted"
        assert data["submission_approved"] is True
        assert data["completed_at"] is not None

        print("[PASS] POST /execution/submitted")

        # -----------------------------------------------------
        # 13. Submitted -> executing must fail
        # -----------------------------------------------------

        response = client.post(
            f"/api/applications/{application_id}/execution/start"
        )

        assert response.status_code == 400

        print("[PASS] submitted -> executing blocked")

        # -----------------------------------------------------
        # 14. Submitted -> failed must fail
        # -----------------------------------------------------

        response = client.post(
            f"/api/applications/{application_id}/execution/failed",
            json={
                "failure_reason": "Invalid late failure.",
            },
        )

        assert response.status_code == 400

        print("[PASS] submitted -> failed blocked")

        # -----------------------------------------------------
        # 15. Submitted -> human intervention must fail
        # -----------------------------------------------------

        response = client.post(
            f"/api/applications/{application_id}/execution/needs-human",
            json={
                "current_action":
                    "unexpected_intervention",
            },
        )

        assert response.status_code == 400

        print(
            "[PASS] submitted -> needs_human blocked"
        )

        # -----------------------------------------------------
        # 16. GET execution
        # -----------------------------------------------------

        response = client.get(
            f"/api/applications/{application_id}/execution"
        )

        assert response.status_code == 200, response.text

        data = response.json()

        assert data["status"] == "submitted"
        assert data["submission_approved"] is True

        print("[PASS] GET /execution -> submitted")

        # -----------------------------------------------------
        # Final database verification
        # -----------------------------------------------------

        execution = get_execution(application_id)

        assert execution is not None
        assert execution.status == "submitted"
        assert execution.submission_approved is True
        assert execution.completed_at is not None

        print(
            "[PASS] Database state -> submitted"
        )

        print(
            "\n=== API TEST COMPLETE ===\n"
        )

    finally:
        if application_id is not None:
            cleanup_test_application(
                application_id
            )

            print(
                "Temporary execution API test data "
                "cleaned up."
            )


if __name__ == "__main__":
    main()