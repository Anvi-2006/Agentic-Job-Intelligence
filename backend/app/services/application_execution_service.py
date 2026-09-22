from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.models.application import Application
from backend.app.models.application_execution import ApplicationExecution
from backend.app.services.execution_event_service import record_execution_event


EXECUTION_STATUS_READY = "ready"
EXECUTION_STATUS_EXECUTING = "executing"
EXECUTION_STATUS_SUBMITTED = "submitted"
EXECUTION_STATUS_NEEDS_HUMAN = "needs_human"
EXECUTION_STATUS_FAILED = "failed"


ALLOWED_TRANSITIONS = {
    EXECUTION_STATUS_READY: {
        EXECUTION_STATUS_EXECUTING,
    },
    EXECUTION_STATUS_EXECUTING: {
        EXECUTION_STATUS_NEEDS_HUMAN,
        EXECUTION_STATUS_FAILED,
        EXECUTION_STATUS_SUBMITTED,
    },
    EXECUTION_STATUS_NEEDS_HUMAN: {
        EXECUTION_STATUS_EXECUTING,
    },
    EXECUTION_STATUS_FAILED: {
        EXECUTION_STATUS_READY,
    },
    EXECUTION_STATUS_SUBMITTED: set(),
}


def create_application_execution(
    db: Session,
    application_id: UUID,
) -> dict:
    application = db.get(Application, application_id)

    if application is None:
        raise ValueError("Application not found.")

    if application.status.lower() != "approved":
        raise ValueError(
            "Application execution is only allowed for approved applications."
        )

    existing_execution = _get_existing_execution(
        db,
        application_id,
    )

    if existing_execution is not None:
        return _execution_response(existing_execution)

    execution = ApplicationExecution(
        application_id=application_id,
        status=EXECUTION_STATUS_READY,
        current_step=0,
        current_action="ready",
        submission_approved=False,
    )

    db.add(execution)
    db.commit()
    db.refresh(execution)

    return _execution_response(execution)


def get_application_execution(
    db: Session,
    application_id: UUID,
) -> dict:
    execution = _get_execution(db, application_id)

    return _execution_response(execution)


def start_application_execution(
    db: Session,
    application_id: UUID,
) -> dict:
    execution = _get_execution(db, application_id)

    _require_transition(
        execution.status,
        EXECUTION_STATUS_EXECUTING,
    )

    execution.status = EXECUTION_STATUS_EXECUTING
    execution.current_action = "starting"

    # A fresh execution run must always require
    # fresh submission approval.
    execution.submission_approved = False

    if execution.started_at is None:
        execution.started_at = func.now()

    record_execution_event(
        db=db,
        execution_id=execution.id,
        event_type="EXECUTION_STARTED",
        step=execution.current_step,
        action="starting",
        details="Application execution started.",
        success=True,
        commit=False,
    )

    db.commit()
    db.refresh(execution)

    return _execution_response(execution)


def request_submission_approval(
    db: Session,
    application_id: UUID,
) -> dict:
    execution = _get_execution(db, application_id)

    _require_transition(
        execution.status,
        EXECUTION_STATUS_NEEDS_HUMAN,
    )

    execution.status = EXECUTION_STATUS_NEEDS_HUMAN
    execution.current_action = "submission_approval_required"

    # Requesting approval does NOT mean approval was granted.
    execution.submission_approved = False

    record_execution_event(
        db=db,
        execution_id=execution.id,
        event_type="SUBMISSION_APPROVAL_REQUIRED",
        step=execution.current_step + 1,
        action="submission_approval_required",
        details=(
            "Application fields are complete. "
            "Human approval is required before application submission."
        ),
        success=True,
        commit=False,
    )

    db.commit()
    db.refresh(execution)

    return _execution_response(execution)


def approve_application_submission(
    db: Session,
    application_id: UUID,
) -> dict:
    execution = _get_execution(
        db,
        application_id,
    )

    if execution.status != EXECUTION_STATUS_NEEDS_HUMAN:
        raise ValueError(
            "Submission approval can only be granted while "
            "human approval is required."
        )

    if execution.current_action != "submission_approval_required":
        raise ValueError(
            "Execution is waiting for a different type of human intervention."
        )

    execution.submission_approved = True

    _require_transition(
        execution.status,
        EXECUTION_STATUS_EXECUTING,
    )

    execution.status = EXECUTION_STATUS_EXECUTING
    execution.current_action = "submission_approved"

    record_execution_event(
        db=db,
        execution_id=execution.id,
        event_type="SUBMISSION_APPROVED",
        step=execution.current_step + 1,
        action="submission_approved",
        details=(
            "Human approved final application submission."
        ),
        success=True,
        commit=False,
    )

    db.commit()
    db.refresh(execution)

    return _execution_response(execution)


def mark_execution_submitted(
    db: Session,
    application_id: UUID,
) -> dict:
    execution = _get_execution(
        db,
        application_id,
    )

    if not execution.submission_approved:
        raise ValueError(
            "Application submission requires explicit human approval."
        )

    _require_transition(
        execution.status,
        EXECUTION_STATUS_SUBMITTED,
    )

    execution.status = EXECUTION_STATUS_SUBMITTED
    execution.current_action = "submitted"
    execution.completed_at = func.now()

    record_execution_event(
        db=db,
        execution_id=execution.id,
        event_type="APPLICATION_SUBMITTED",
        step=execution.current_step,
        action="submitted",
        details=(
            "Application execution completed and application submitted."
        ),
        success=True,
        commit=False,
    )

    db.commit()
    db.refresh(execution)

    return _execution_response(execution)


def mark_execution_needs_human(
    db: Session,
    application_id: UUID,
    current_action: str,
) -> dict:
    execution = _get_execution(
        db,
        application_id,
    )

    _require_transition(
        execution.status,
        EXECUTION_STATUS_NEEDS_HUMAN,
    )

    execution.status = EXECUTION_STATUS_NEEDS_HUMAN
    execution.current_action = current_action

    record_execution_event(
        db=db,
        execution_id=execution.id,
        event_type="HUMAN_INTERVENTION_REQUIRED",
        step=execution.current_step + 1,
        action=current_action,
        details="Execution requires human intervention.",
        success=True,
        commit=False,
    )

    db.commit()
    db.refresh(execution)

    return _execution_response(execution)


def resume_application_execution(
    db: Session,
    application_id: UUID,
) -> dict:
    execution = _get_execution(
        db,
        application_id,
    )

    _require_transition(
        execution.status,
        EXECUTION_STATUS_EXECUTING,
    )

    execution.status = EXECUTION_STATUS_EXECUTING
    execution.current_action = "resuming"

    record_execution_event(
        db=db,
        execution_id=execution.id,
        event_type="EXECUTION_RESUMED",
        step=execution.current_step + 2,
        action="resuming",
        details="Application execution resumed after human intervention.",
        success=True,
        commit=False,
    )

    db.commit()
    db.refresh(execution)

    return _execution_response(execution)


def mark_execution_failed(
    db: Session,
    application_id: UUID,
    failure_reason: str,
) -> dict:
    execution = _get_execution(
        db,
        application_id,
    )

    _require_transition(
        execution.status,
        EXECUTION_STATUS_FAILED,
    )

    execution.status = EXECUTION_STATUS_FAILED
    execution.failure_reason = failure_reason
    execution.current_action = "failed"
    execution.completed_at = func.now()

    # A failed execution must never retain submission approval.
    execution.submission_approved = False

    record_execution_event(
        db=db,
        execution_id=execution.id,
        event_type="EXECUTION_FAILED",
        step=execution.current_step,
        action="failed",
        details=failure_reason,
        success=False,
        commit=False,
    )

    db.commit()
    db.refresh(execution)

    return _execution_response(execution)


def retry_failed_execution(
    db: Session,
    application_id: UUID,
) -> dict:
    execution = _get_execution(
        db,
        application_id,
    )

    _require_transition(
        execution.status,
        EXECUTION_STATUS_READY,
    )

    execution.status = EXECUTION_STATUS_READY
    execution.current_action = "retry_ready"
    execution.failure_reason = None
    execution.completed_at = None

    # Retry requires fresh submission approval.
    execution.submission_approved = False

    record_execution_event(
        db=db,
        execution_id=execution.id,
        event_type="EXECUTION_RETRY_READY",
        step=execution.current_step,
        action="retry_ready",
        details="Failed execution reset and is ready for retry.",
        success=True,
        commit=False,
    )

    db.commit()
    db.refresh(execution)

    return _execution_response(execution)


def update_execution_step(
    db: Session,
    application_id: UUID,
    current_step: int,
    current_action: str,
) -> dict:
    execution = _get_execution(
        db,
        application_id,
    )

    if execution.status != EXECUTION_STATUS_EXECUTING:
        raise ValueError(
            "Execution steps can only be updated while execution is in progress."
        )

    if current_step < 0:
        raise ValueError(
            "Execution step cannot be negative."
        )

    execution.current_step = current_step
    execution.current_action = current_action

    db.commit()
    db.refresh(execution)

    return _execution_response(execution)


def _get_existing_execution(
    db: Session,
    application_id: UUID,
) -> ApplicationExecution | None:
    return (
        db.query(ApplicationExecution)
        .filter(
            ApplicationExecution.application_id == application_id,
        )
        .first()
    )


def _get_execution(
    db: Session,
    application_id: UUID,
) -> ApplicationExecution:
    execution = _get_existing_execution(
        db,
        application_id,
    )

    if execution is None:
        raise ValueError(
            "Application execution not found."
        )

    return execution


def _require_transition(
    current_status: str,
    next_status: str,
) -> None:
    allowed_states = ALLOWED_TRANSITIONS.get(
        current_status,
        set(),
    )

    if next_status not in allowed_states:
        raise ValueError(
            f"Invalid execution state transition: "
            f"{current_status} -> {next_status}."
        )


def _execution_response(
    execution: ApplicationExecution,
) -> dict:
    return {
        "execution_id": str(execution.id),
        "application_id": str(execution.application_id),
        "status": execution.status,
        "current_step": execution.current_step,
        "current_action": execution.current_action,
        "submission_approved": execution.submission_approved,
        "failure_reason": execution.failure_reason,
        "started_at": execution.started_at,
        "completed_at": execution.completed_at,
        "created_at": execution.created_at,
        "updated_at": execution.updated_at,
    }