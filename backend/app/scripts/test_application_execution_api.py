from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models.application import Application
from backend.app.models.application_execution import ApplicationExecution
from backend.app.models.application_package import ApplicationPackage
from backend.app.models.execution_event import ExecutionEvent


SOURCE_APPLICATION_ID = UUID(
    "a9234440-f94f-4650-889f-b4d3c463ffd5"
)

SCRIPT_DIRECTORY = Path(__file__).resolve().parent

HUMAN_INTERVENTION_FORM = (
    SCRIPT_DIRECTORY
    / "browser_execution_human_intervention_test.html"
)

RESOLVED_FORM = (
    SCRIPT_DIRECTORY
    / "browser_execution_resolved_test.html"
)

client = TestClient(app)


def main() -> None:
    db = SessionLocal()

    temporary_application = None
    temporary_execution = None
    temporary_package = None

    try:
        source_application = db.get(
            Application,
            SOURCE_APPLICATION_ID,
        )

        if source_application is None:
            raise ValueError(
                "Source application not found."
            )

        source_package = (
            db.query(ApplicationPackage)
            .filter(
                ApplicationPackage.application_id
                == SOURCE_APPLICATION_ID,
            )
            .first()
        )

        if source_package is None:
            raise ValueError(
                "Source application package not found."
            )

        temporary_application = Application(
            candidate_id=source_application.candidate_id,
            job_id=source_application.job_id,
            status="approved",
            fit_score=source_application.fit_score,
            recommendation=source_application.recommendation,
            reviewer_note=(
                "Temporary API integration test."
            ),
        )

        db.add(temporary_application)
        db.flush()

        temporary_package = ApplicationPackage(
            application_id=temporary_application.id,
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

        db.add(temporary_package)
        db.commit()

        application_id = str(
            temporary_application.id
        )

        print(
            f"Temporary application: "
            f"{application_id}"
        )

        # -------------------------------------------------
        # 1. CREATE EXECUTION
        # -------------------------------------------------

        response = client.post(
            f"/api/applications/{application_id}/execution"
        )

        print(
            "Create execution:",
            response.status_code,
        )

        assert response.status_code == 200

        execution_data = response.json()

        assert execution_data["status"] == "ready"

        temporary_execution = db.get(
            ApplicationExecution,
            UUID(
                execution_data["execution_id"]
            ),
        )

        print(
            "Create execution API: PASS"
        )

        # -------------------------------------------------
        # 2. START EXECUTION
        # -------------------------------------------------

        response = client.post(
            f"/api/applications/{application_id}/execution/start"
        )

        print(
            "Start execution:",
            response.status_code,
        )

        assert response.status_code == 200
        assert response.json()["status"] == "executing"

        print(
            "Start execution API: PASS"
        )

        # -------------------------------------------------
        # 3. BROWSER EXECUTION → NEEDS HUMAN
        # -------------------------------------------------

        unresolved_url = (
            HUMAN_INTERVENTION_FORM
            .resolve()
            .as_uri()
        )

        response = client.post(
            f"/api/applications/{application_id}/execution/browser",
            json={
                "application_url": unresolved_url,
                "headless": True,
            },
        )

        print(
            "Browser execution:",
            response.status_code,
        )

        assert response.status_code == 200

        browser_data = response.json()

        assert (
            browser_data["status"]
            == "needs_human"
        )

        assert (
            browser_data["execution"][
                "current_action"
            ]
            == "browser_human_intervention"
        )

        assert (
            browser_data["plan"][
                "human_intervention_required"
            ]
            is True
        )

        print(
            "Browser NEEDS_HUMAN API: PASS"
        )

        # -------------------------------------------------
        # 4. RESUME THROUGH API
        # -------------------------------------------------

        response = client.post(
            f"/api/applications/{application_id}/execution/resume"
        )

        print(
            "Resume execution:",
            response.status_code,
        )

        assert response.status_code == 200
        assert response.json()["status"] == "executing"

        print(
            "Resume execution API: PASS"
        )

        # -------------------------------------------------
        # 5. BROWSER EXECUTION AFTER RESUME
        # -------------------------------------------------

        resolved_url = (
            RESOLVED_FORM
            .resolve()
            .as_uri()
        )

        response = client.post(
            f"/api/applications/{application_id}/execution/browser",
            json={
                "application_url": resolved_url,
                "headless": True,
            },
        )

        print(
            "Resolved browser execution:",
            response.status_code,
        )

        assert response.status_code == 200

        final_browser_data = response.json()

        assert (
            final_browser_data["status"]
            == "executing"
        )

        assert (
            final_browser_data["execution"][
                "current_action"
            ]
            == "browser_fields_completed"
        )

        executed_actions = (
            final_browser_data[
                "execution_result"
            ]["executed_actions"]
        )

        assert len(executed_actions) == 4

        print(
            "Browser execution after resume: PASS"
        )

        # -------------------------------------------------
        # 6. EXECUTION EVENTS API
        # -------------------------------------------------

        response = client.get(
            f"/api/applications/{application_id}/execution/events"
        )

        print(
            "Execution events:",
            response.status_code,
        )

        assert response.status_code == 200

        events = response.json()

        event_types = [
            event["event_type"]
            for event in events
        ]

        assert (
            "EXECUTION_STARTED"
            in event_types
        )

        assert (
            "BROWSER_HUMAN_INTERVENTION_REQUIRED"
            in event_types
        )

        assert (
            "EXECUTION_RESUMED"
            in event_types
        )

        assert (
            event_types.count(
                "BROWSER_ACTION_EXECUTED"
            )
            == 4
        )

        assert (
            "BROWSER_FIELDS_COMPLETED"
            in event_types
        )

        print(
            "Execution events API: PASS"
        )

        print()
        print(
            "FULL APPLICATION EXECUTION API "
            "INTEGRATION TEST: PASS"
        )

    finally:
        if temporary_execution is not None:
            db.query(ExecutionEvent).filter(
                ExecutionEvent.execution_id
                == temporary_execution.id,
            ).delete(
                synchronize_session=False,
            )

            db.query(ApplicationExecution).filter(
                ApplicationExecution.id
                == temporary_execution.id,
            ).delete(
                synchronize_session=False,
            )

        if temporary_package is not None:
            db.query(ApplicationPackage).filter(
                ApplicationPackage.id
                == temporary_package.id,
            ).delete(
                synchronize_session=False,
            )

        if temporary_application is not None:
            db.query(Application).filter(
                Application.id
                == temporary_application.id,
            ).delete(
                synchronize_session=False,
            )

        db.commit()
        db.close()


if __name__ == "__main__":
    main()