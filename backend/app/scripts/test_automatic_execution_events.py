from backend.app.core.database import SessionLocal
from backend.app.models.application import Application
from backend.app.models.application_execution import ApplicationExecution
from backend.app.models.execution_event import ExecutionEvent
from backend.app.services.application_execution_service import (
    create_application_execution,
    start_application_execution,
)


db = SessionLocal()
temporary_application_id = None

try:
    source_application = (
        db.query(Application)
        .filter(
            Application.id
            == "a9234440-f94f-4650-889f-b4d3c463ffd5"
        )
        .first()
    )

    if source_application is None:
        raise RuntimeError("Source approved application not found.")

    temporary_application = Application(
        candidate_id=source_application.candidate_id,
        job_id=source_application.job_id,
        fit_score=source_application.fit_score,
        recommendation=source_application.recommendation,
        status="approved",
        reviewer_note="Temporary automatic execution event verification.",
    )

    db.add(temporary_application)
    db.commit()
    db.refresh(temporary_application)

    temporary_application_id = temporary_application.id

    print(
        f"Temporary application created: "
        f"{temporary_application_id}"
    )

    execution = create_application_execution(
        db=db,
        application_id=temporary_application_id,
    )

    print(f"Execution status: {execution['status']}")

    if execution["status"] != "ready":
        raise RuntimeError(
            f"Expected ready execution, got {execution['status']}"
        )

    started = start_application_execution(
        db=db,
        application_id=temporary_application_id,
    )

    print(f"Started execution status: {started['status']}")

    if started["status"] != "executing":
        raise RuntimeError(
            f"Expected executing status, got {started['status']}"
        )

    execution_id = started["execution_id"]

    event = (
        db.query(ExecutionEvent)
        .filter(
            ExecutionEvent.execution_id == execution_id,
            ExecutionEvent.event_type == "EXECUTION_STARTED",
        )
        .order_by(ExecutionEvent.created_at.desc())
        .first()
    )

    if event is None:
        raise RuntimeError(
            "EXECUTION_STARTED audit event was not created."
        )

    print("[PASS] EXECUTION_STARTED audit event created")
    print(f"Event ID: {event.id}")
    print(f"Step: {event.step}")
    print(f"Action: {event.action}")
    print(f"Success: {event.success}")

finally:
    if temporary_application_id is not None:
        db.rollback()

        execution = (
            db.query(ApplicationExecution)
            .filter(
                ApplicationExecution.application_id
                == temporary_application_id
            )
            .first()
        )

        if execution is not None:
            db.query(ExecutionEvent).filter(
                ExecutionEvent.execution_id == execution.id
            ).delete(synchronize_session=False)

            db.delete(execution)
            db.flush()

        db.query(Application).filter(
            Application.id == temporary_application_id
        ).delete(synchronize_session=False)

        db.commit()

        print(
            f"Temporary application removed: "
            f"{temporary_application_id}"
        )

    db.close()
