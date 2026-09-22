from uuid import UUID

from backend.app.core.database import SessionLocal
from backend.app.models.application import Application
from backend.app.models.application_execution import ApplicationExecution
from backend.app.models.application_package import ApplicationPackage
from backend.app.models.execution_event import ExecutionEvent
from backend.app.services.application_execution_service import (
    create_application_execution,
    mark_execution_needs_human,
    resume_application_execution,
    start_application_execution,
)


SOURCE_APPLICATION_ID = UUID(
    "a9234440-f94f-4650-889f-b4d3c463ffd5"
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
            raise ValueError("Source application not found.")

        source_package = (
            db.query(ApplicationPackage)
            .filter(
                ApplicationPackage.application_id
                == SOURCE_APPLICATION_ID,
            )
            .first()
        )

        if source_package is None:
            raise ValueError("Source application package not found.")

        temporary_application = Application(
            candidate_id=source_application.candidate_id,
            job_id=source_application.job_id,
            status="approved",
            fit_score=source_application.fit_score,
            recommendation=source_application.recommendation,
            reviewer_note="Temporary resume integration test.",
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

        needs_human = mark_execution_needs_human(
            db=db,
            application_id=temporary_application.id,
            current_action="browser_human_intervention",
        )

        print(
            f"Needs-human status: "
            f"{needs_human['status']}"
        )

        assert needs_human["status"] == "needs_human"
        assert (
            needs_human["current_action"]
            == "browser_human_intervention"
        )

        resumed = resume_application_execution(
            db=db,
            application_id=temporary_application.id,
        )

        print(
            f"Resumed execution status: "
            f"{resumed['status']}"
        )

        print(
            f"Resumed execution action: "
            f"{resumed['current_action']}"
        )

        assert resumed["status"] == "executing"
        assert resumed["current_action"] == "resuming"

        events = (
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

        for event in events:
            print(
                event.step,
                event.event_type,
                event.action,
            )

        event_types = [
            event.event_type
            for event in events
        ]

        assert "EXECUTION_STARTED" in event_types
        assert (
            "HUMAN_INTERVENTION_REQUIRED"
            in event_types
        )
        assert "EXECUTION_RESUMED" in event_types

        print(
            "HUMAN RESOLUTION / RESUME integration test: PASS"
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
