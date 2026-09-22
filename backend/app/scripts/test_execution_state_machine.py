from uuid import UUID

from backend.app.core.database import SessionLocal
from backend.app.models.application import Application
from backend.app.models.application_execution import ApplicationExecution
from backend.app.services.application_execution_service import (
    create_application_execution,
    start_application_execution,
    mark_execution_submitted,
    mark_execution_needs_human,
    mark_execution_failed,
)


APPLICATION_ID = UUID(
    "a9234440-f94f-4650-889f-b4d3c463ffd5"
)


def cleanup_test_execution(db):
    db.query(ApplicationExecution).filter(
        ApplicationExecution.application_id == APPLICATION_ID
    ).delete()

    db.commit()


def main():
    db = SessionLocal()

    try:
        application = db.get(Application, APPLICATION_ID)

        if application is None:
            raise RuntimeError("Application not found.")

        if application.status != "approved":
            raise RuntimeError(
                f"Application must be approved. "
                f"Current status: {application.status}"
            )

        print("\n=== APPLICATION EXECUTION STATE MACHINE TEST ===\n")

        # ---------------------------------------------------------
        # Test 1: APPROVED -> READY
        # ---------------------------------------------------------

        cleanup_test_execution(db)

        execution = create_application_execution(
            db=db,
            application_id=APPLICATION_ID,
        )

        assert execution["status"] == "ready"

        print("[PASS] approved -> ready")

        # ---------------------------------------------------------
        # Test 2: READY -> EXECUTING
        # ---------------------------------------------------------

        execution = start_application_execution(
            db=db,
            application_id=APPLICATION_ID,
        )

        assert execution["status"] == "executing"

        print("[PASS] ready -> executing")

        # ---------------------------------------------------------
        # Test 3: EXECUTING -> NEEDS_HUMAN
        # ---------------------------------------------------------

        execution = mark_execution_needs_human(
            db=db,
            application_id=APPLICATION_ID,
            current_action="captcha_detected",
        )

        assert execution["status"] == "needs_human"
        assert execution["current_action"] == "captcha_detected"

        print("[PASS] executing -> needs_human")

        # ---------------------------------------------------------
        # Test 4: NEEDS_HUMAN cannot directly submit
        # ---------------------------------------------------------

        try:
            mark_execution_submitted(
                db=db,
                application_id=APPLICATION_ID,
            )

            print(
                "[FAIL] needs_human -> submitted "
                "(transition should be blocked)"
            )

        except ValueError:
            print(
                "[PASS] needs_human -> submitted "
                "(correctly blocked)"
            )

        # ---------------------------------------------------------
        # Test 5: Reset and test EXECUTING -> FAILED
        # ---------------------------------------------------------

        cleanup_test_execution(db)

        create_application_execution(
            db=db,
            application_id=APPLICATION_ID,
        )

        start_application_execution(
            db=db,
            application_id=APPLICATION_ID,
        )

        execution = mark_execution_failed(
            db=db,
            application_id=APPLICATION_ID,
            failure_reason="Job portal unavailable.",
        )

        assert execution["status"] == "failed"
        assert execution["failure_reason"] == "Job portal unavailable."

        print("[PASS] executing -> failed")

        # ---------------------------------------------------------
        # Test 6: FAILED cannot submit
        # ---------------------------------------------------------

        try:
            mark_execution_submitted(
                db=db,
                application_id=APPLICATION_ID,
            )

            print(
                "[FAIL] failed -> submitted "
                "(transition should be blocked)"
            )

        except ValueError:
            print(
                "[PASS] failed -> submitted "
                "(correctly blocked)"
            )

        # ---------------------------------------------------------
        # Test 7: Reset and test EXECUTING -> SUBMITTED
        # ---------------------------------------------------------

        cleanup_test_execution(db)

        create_application_execution(
            db=db,
            application_id=APPLICATION_ID,
        )

        start_application_execution(
            db=db,
            application_id=APPLICATION_ID,
        )

        execution = mark_execution_submitted(
            db=db,
            application_id=APPLICATION_ID,
        )

        assert execution["status"] == "submitted"

        print("[PASS] executing -> submitted")

        # ---------------------------------------------------------
        # Test 8: SUBMITTED cannot execute again
        # ---------------------------------------------------------

        try:
            start_application_execution(
                db=db,
                application_id=APPLICATION_ID,
            )

            print(
                "[FAIL] submitted -> executing "
                "(transition should be blocked)"
            )

        except ValueError:
            print(
                "[PASS] submitted -> executing "
                "(correctly blocked)"
            )

        # ---------------------------------------------------------
        # Test 9: SUBMITTED cannot fail
        # ---------------------------------------------------------

        try:
            mark_execution_failed(
                db=db,
                application_id=APPLICATION_ID,
                failure_reason="Late failure.",
            )

            print(
                "[FAIL] submitted -> failed "
                "(transition should be blocked)"
            )

        except ValueError:
            print(
                "[PASS] submitted -> failed "
                "(correctly blocked)"
            )

        print("\n=== STATE MACHINE TEST COMPLETE ===\n")

    finally:
        db.close()


if __name__ == "__main__":
    main()