from pathlib import Path
from uuid import uuid4

from backend.app.core.database import SessionLocal
from backend.app.models.application import Application
from backend.app.models.application_package import ApplicationPackage
from backend.app.models.human_input_request import HumanInputRequest
from backend.app.models.execution_event import ExecutionEvent
from backend.app.models.application_execution import (
    ApplicationExecution,
)
from backend.app.services.application_execution_service import (
    create_application_execution,
    start_application_execution,
)
from backend.app.services.application_browser_execution_service import (
    execute_application_browser_step,
)


TEST_PAGE = (
    Path(__file__).resolve().parent
    / "browser_execution_human_intervention_test.html"
)


def main() -> None:
    db = SessionLocal()

    temporary_application = None
    temporary_package = None
    temporary_execution = None

    try:
        source_application = (
            db.query(Application)
            .filter(
                Application.id
                == "69872582-adea-400b-be7f-e054780165e5"
            )
            .first()
        )

        if source_application is None:
            raise RuntimeError(
                "Source application not found."
            )

        source_package = (
            db.query(ApplicationPackage)
            .filter(
                ApplicationPackage.application_id
                == source_application.id,
            )
            .first()
        )

        if source_package is None:
            raise RuntimeError(
                "Source application package not found."
            )

        print(
            "Source application:",
            source_application.id,
        )

        print(
            "Source package:",
            source_package.id,
        )

        print(
            "Source package valid:",
            source_package.is_valid,
        )

        temporary_application = Application(
            id=uuid4(),
            candidate_id=source_application.candidate_id,
            job_id=source_application.job_id,
            fit_score=source_application.fit_score,
            recommendation=source_application.recommendation,
            status="approved",
            reviewer_note=(
                "Temporary application for "
                "NEEDS_HUMAN integration testing."
            ),
        )

        db.add(temporary_application)
        db.flush()

        temporary_package = ApplicationPackage(
            id=uuid4(),
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
            "Temporary application:",
            temporary_application.id,
        )

        print(
            "Temporary package:",
            temporary_package.id,
        )

        execution = create_application_execution(
            db=db,
            application_id=temporary_application.id,
        )

        temporary_execution = (
            db.query(ApplicationExecution)
            .filter(
                ApplicationExecution.application_id
                == temporary_application.id,
            )
            .first()
        )

        if temporary_execution is None:
            raise RuntimeError(
                "Application execution was not created."
            )

        print(
            "Initial execution status:",
            temporary_execution.status,
        )

        start_application_execution(
            db=db,
            application_id=temporary_application.id,
        )

        print(
            "Started execution status:",
            temporary_execution.status,
        )

        application_url = TEST_PAGE.resolve().as_uri()

        print(
            "Application URL:",
            application_url,
        )

        result = execute_application_browser_step(
            application_id=temporary_application.id,
            application_url=application_url,
            headless=True,
        )

        db.expire_all()

        execution_row = (
            db.query(
                __import__(
                    "backend.app.models.application_execution",
                    fromlist=["ApplicationExecution"],
                ).ApplicationExecution
            )
            .filter(
                __import__(
                    "backend.app.models.application_execution",
                    fromlist=["ApplicationExecution"],
                ).ApplicationExecution.application_id
                == temporary_application.id,
            )
            .first()
        )

        print(
            "Browser execution status:",
            result["status"],
        )

        print(
            "Execution status after browser run:",
            execution_row.status,
        )

        print(
            "Execution action:",
            execution_row.current_action,
        )

        print(
            "Human intervention required:",
            result["plan"]["human_intervention_required"],
        )

        print(
            "Executed actions:",
            result.get(
                "execution_result",
                {},
            ).get(
                "executed_actions",
                [],
            ),
        )

        assert result["status"] == "needs_human"

        assert (
            execution_row.status
            == "needs_human"
        )

        assert (
            execution_row.current_action
            == "browser_human_intervention"
        )

        assert (
            result["plan"][
                "human_intervention_required"
            ]
            is True
        )

        assert (
            result.get(
                "execution_result",
                {},
            ).get(
                "executed_actions",
                [],
            )
            == []
        )

        events = (
            db.query(ExecutionEvent)
            .filter(
                ExecutionEvent.execution_id
                == execution_row.id,
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
                {
                    "event_type": event.event_type,
                    "step": event.step,
                    "action": event.action,
                    "success": event.success,
                }
            )

        event_types = [
            event.event_type
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

        print(
            "NEEDS_HUMAN integration test: PASS"
        )

    finally:
        if temporary_execution is not None:
            db.query(ExecutionEvent).filter(
                ExecutionEvent.execution_id == temporary_execution.id,
            ).delete(synchronize_session=False)

            db.query(HumanInputRequest).filter(
                HumanInputRequest.execution_id == temporary_execution.id,
            ).delete(synchronize_session=False)

            db.query(ApplicationExecution).filter(
                ApplicationExecution.id == temporary_execution.id,
            ).delete(synchronize_session=False)

        if temporary_package is not None:
            db.query(ApplicationPackage).filter(
                ApplicationPackage.id == temporary_package.id,
            ).delete(synchronize_session=False)

        if temporary_application is not None:
            db.query(Application).filter(
                Application.id == temporary_application.id,
            ).delete(synchronize_session=False)

        db.commit()

        print(
            "Temporary NEEDS_HUMAN data cleanup: PASS"
        )

        db.close()


if __name__ == "__main__":
    main()
