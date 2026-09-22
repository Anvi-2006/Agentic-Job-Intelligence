import uuid
from uuid import UUID

from backend.app.core.database import SessionLocal
from backend.app.models.application import Application
from backend.app.models.application_execution import ApplicationExecution
from backend.app.models.application_package import ApplicationPackage
from backend.app.models.execution_event import ExecutionEvent
from backend.app.models.human_input_request import HumanInputRequest
from backend.app.services.application_execution_service import (
    approve_application_submission,
    create_application_execution,
    mark_execution_submitted,
    request_submission_approval,
    start_application_execution,
)
from backend.app.services.application_submission_service import (
    validate_application_submission,
)

SOURCE_APPLICATION_ID = UUID(
    "a9234440-f94f-4650-889f-b4d3c463ffd5"
)


def create_test_application(db):
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
            "Source application must be approved."
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
        reviewer_note="Temporary submission approval gate test.",
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
            HumanInputRequest.execution_id.in_(execution_ids)
        ).delete(
            synchronize_session=False
        )

        db.query(ExecutionEvent).filter(
            ExecutionEvent.execution_id.in_(execution_ids)
        ).delete(
            synchronize_session=False
        )

        db.query(ApplicationExecution).filter(
            ApplicationExecution.id.in_(execution_ids)
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


def main():
    db = SessionLocal()
    test_application_id = None

    try:
        print("\n=== SUBMISSION APPROVAL GATE TEST ===\n")

        test_application_id = create_test_application(db)

        print(
            "[PASS] temporary approved application created"
        )

        execution = create_application_execution(
            db=db,
            application_id=test_application_id,
        )

        assert execution["status"] == "ready"
        assert execution["submission_approved"] is False

        print(
            "[PASS] execution created with "
            "submission_approved=False"
        )

        execution = start_application_execution(
            db=db,
            application_id=test_application_id,
        )

        assert execution["status"] == "executing"
        assert execution["submission_approved"] is False

        print(
            "[PASS] ready -> executing with "
            "submission approval still false"
        )

        execution = request_submission_approval(
            db=db,
            application_id=test_application_id,
        )

        assert execution["status"] == "needs_human"
        assert (
            execution["current_action"]
            == "submission_approval_required"
        )
        assert execution["submission_approved"] is False

        print(
            "[PASS] submission approval requested "
            "and execution moved to needs_human"
        )

        try:
            mark_execution_submitted(
                db=db,
                application_id=test_application_id,
            )

            print(
                "[FAIL] submission allowed before "
                "human approval"
            )

        except ValueError:
            db.rollback()

            print(
                "[PASS] submission blocked before "
                "human approval"
            )

        try:
            validate_application_submission(
                db=db,
                application_id=test_application_id,
            )

            print(
                "[FAIL] validation allowed before "
                "human approval"
            )

        except ValueError:
            db.rollback()

            print(
                "[PASS] validation blocked before "
                "human approval"
            )

        execution = approve_application_submission(
            db=db,
            application_id=test_application_id,
        )

        assert execution["status"] == "executing"
        assert (
            execution["current_action"]
            == "submission_approved"
        )
        assert execution["submission_approved"] is True

        print(
            "[PASS] human explicitly approved submission"
        )

        validation = validate_application_submission(
            db=db,
            application_id=test_application_id,
        )

        assert validation["approved"] is True
        assert validation["submission_approval"] is True
        assert validation["submission_allowed"] is True

        print(
            "[PASS] submission validation allowed "
            "after explicit approval"
        )

        execution = mark_execution_submitted(
            db=db,
            application_id=test_application_id,
        )

        assert execution["status"] == "submitted"
        assert execution["submission_approved"] is True

        print(
            "[PASS] approved execution -> submitted"
        )

        print(
            "\n=== SUBMISSION APPROVAL GATE TEST COMPLETE ===\n"
        )

    finally:
        if test_application_id is not None:
            cleanup_test_application(
                db,
                test_application_id,
            )

        db.close()


if __name__ == "__main__":
    main()