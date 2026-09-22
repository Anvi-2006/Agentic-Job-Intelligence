from pathlib import Path
from uuid import UUID

from backend.app.core.database import SessionLocal
from backend.app.models.application import Application
from backend.app.models.application_execution import ApplicationExecution
from backend.app.models.application_package import ApplicationPackage
from backend.app.models.execution_event import ExecutionEvent
from backend.app.services.application_browser_execution_service import (
    execute_application_browser_step,
)
from backend.app.services.application_execution_service import (
    create_application_execution,
    resume_application_execution,
    start_application_execution,
)


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


def main() -> None:
    db = SessionLocal()

    temporary_application = None
    temporary_package = None
    temporary_execution = None

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
                "Temporary full human-in-the-loop "
                "browser execution test."
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

        print(
            f"Temporary application: "
            f"{temporary_application.id}"
        )

        print(
            f"Temporary package: "
            f"{temporary_package.id}"
        )

        execution = create_application_execution(
            db=db,
            application_id=temporary_application.id,
        )

        temporary_execution = db.get(
            ApplicationExecution,
            UUID(execution["execution_id"]),
        )

        print(
            f"Initial execution status: "
            f"{execution['status']}"
        )

        started = start_application_execution(
            db=db,
            application_id=temporary_application.id,
        )

        print(
            f"Started execution status: "
            f"{started['status']}"
        )

        unresolved_url = (
            HUMAN_INTERVENTION_FORM
            .resolve()
            .as_uri()
        )

        print(
            f"Unresolved application URL: "
            f"{unresolved_url}"
        )

        first_run = execute_application_browser_step(
            application_id=temporary_application.id,
            application_url=unresolved_url,
            headless=True,
        )

        print(
            f"First browser execution status: "
            f"{first_run['status']}"
        )

        assert first_run["status"] == "needs_human"
        assert (
            first_run["execution"]["current_action"]
            == "browser_human_intervention"
        )

        assert (
            first_run["plan"][
                "human_intervention_required"
            ]
            is True
        )

        assert (
            first_run["plan"]["actions"][-1][
                "action"
            ]
            == "needs_human"
        )

        print(
            "Human intervention correctly triggered."
        )

        db.expire_all()

        resumed = resume_application_execution(
            db=db,
            application_id=temporary_application.id,
        )

        print(
            f"Resumed execution status: "
            f"{resumed['status']}"
        )

        assert resumed["status"] == "executing"

        resolved_url = (
            RESOLVED_FORM
            .resolve()
            .as_uri()
        )

        print(
            f"Resolved application URL: "
            f"{resolved_url}"
        )

        second_run = execute_application_browser_step(
            application_id=temporary_application.id,
            application_url=resolved_url,
            headless=True,
        )

        print(
            f"Second browser execution status: "
            f"{second_run['status']}"
        )

        assert second_run["status"] == "executing"

        assert (
            second_run["execution"][
                "current_action"
            ]
            == "browser_fields_completed"
        )

        execution_result = second_run.get(
            "execution_result",
            {},
        )

        executed_actions = execution_result.get(
            "executed_actions",
            [],
        )

        print(
            f"Executed actions after resume: "
            f"{len(executed_actions)}"
        )

        assert len(executed_actions) == 4

        event_rows = (
            db.query(ExecutionEvent)
            .filter(
                ExecutionEvent.execution_id
                == temporary_execution.id,
            )
            .order_by(
                ExecutionEvent.step.asc(),
                ExecutionEvent.created_at.asc(),
                ExecutionEvent.id.asc(),
            )
            .all()
        )

        print("Execution events:")

        for event in event_rows:
            print(
                event.step,
                event.event_type,
                event.action,
            )

        event_types = [
            event.event_type
            for event in event_rows
        ]

        assert "EXECUTION_STARTED" in event_types

        assert (
            "BROWSER_HUMAN_INTERVENTION_REQUIRED"
            in event_types
        )

        assert "EXECUTION_RESUMED" in event_types

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
            "FULL HUMAN-IN-THE-LOOP browser "
            "execution test: PASS"
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
