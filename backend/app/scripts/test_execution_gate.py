import uuid
from uuid import UUID

from backend.app.core.database import SessionLocal
from backend.app.models.application import Application
from backend.app.models.application_execution import ApplicationExecution
from backend.app.models.execution_event import ExecutionEvent
from backend.app.models.human_input_request import HumanInputRequest
from backend.app.services.application_execution_service import (
    create_application_execution,
)


SOURCE_APPLICATION_ID = UUID(
    "a9234440-f94f-4650-889f-b4d3c463ffd5"
)


def create_test_applications(db):
    source_application = db.get(
        Application,
        SOURCE_APPLICATION_ID,
    )

    if source_application is None:
        raise RuntimeError(
            "Source application not found."
        )

    approved_application = Application(
        id=uuid.uuid4(),
        candidate_id=source_application.candidate_id,
        job_id=source_application.job_id,
        fit_score=source_application.fit_score,
        recommendation=source_application.recommendation,
        status="approved",
        reviewer_note="Temporary execution gate test.",
    )

    unapproved_application = Application(
        id=uuid.uuid4(),
        candidate_id=source_application.candidate_id,
        job_id=source_application.job_id,
        fit_score=source_application.fit_score,
        recommendation=source_application.recommendation,
        status="pending_review",
        reviewer_note="Temporary execution gate test.",
    )

    db.add(approved_application)
    db.add(unapproved_application)
    db.commit()

    return (
        approved_application.id,
        unapproved_application.id,
    )


def cleanup_test_application(db, application_id):
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

    db.query(Application).filter(
        Application.id == application_id
    ).delete(
        synchronize_session=False
    )


def main():
    db = SessionLocal()

    approved_application_id = None
    unapproved_application_id = None

    try:
        print("\n=== APPLICATION EXECUTION GATE TEST ===\n")

        (
            approved_application_id,
            unapproved_application_id,
        ) = create_test_applications(db)

        # -----------------------------------------------------
        # 1. Unapproved application must be blocked
        # -----------------------------------------------------

        try:
            create_application_execution(
                db=db,
                application_id=unapproved_application_id,
            )

            print(
                "[FAIL] unapproved application "
                "was allowed to execute"
            )

        except ValueError as exc:
            assert (
                str(exc)
                == "Application execution is only allowed "
                   "for approved applications."
            )

            print(
                "[PASS] unapproved application blocked"
            )

        # -----------------------------------------------------
        # 2. Approved application must be allowed
        # -----------------------------------------------------

        result = create_application_execution(
            db=db,
            application_id=approved_application_id,
        )

        assert result["application_id"] == str(
            approved_application_id
        )
        assert result["status"] == "ready"
        assert result["submission_approved"] is False

        print(
            "[PASS] approved application allowed "
            "to create execution"
        )

        print(
            "\n=== EXECUTION GATE TEST COMPLETE ===\n"
        )

    finally:
        if approved_application_id is not None:
            cleanup_test_application(
                db,
                approved_application_id,
            )

        if unapproved_application_id is not None:
            cleanup_test_application(
                db,
                unapproved_application_id,
            )

        db.commit()
        db.close()


if __name__ == "__main__":
    main()