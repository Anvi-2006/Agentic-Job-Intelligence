from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models.application_execution import ApplicationExecution
from backend.app.models.execution_event import ExecutionEvent


def record_execution_event(
    db: Session,
    execution_id: UUID,
    event_type: str,
    step: int,
    action: str,
    details: str | None = None,
    success: bool = True,
    commit: bool = True,
) -> dict:
    execution = db.get(
        ApplicationExecution,
        execution_id,
    )

    if execution is None:
        raise ValueError(
            "Application execution not found."
        )

    if step < 0:
        raise ValueError(
            "Execution event step cannot be negative."
        )

    if not event_type.strip():
        raise ValueError(
            "Execution event type cannot be empty."
        )

    if not action.strip():
        raise ValueError(
            "Execution event action cannot be empty."
        )

    event = ExecutionEvent(
        execution_id=execution_id,
        event_type=event_type.strip(),
        step=step,
        action=action.strip(),
        details=details,
        success=success,
    )

    db.add(event)

    if commit:
        db.commit()
        db.refresh(event)
    else:
        db.flush()

    return _event_response(event)


def get_execution_events(
    db: Session,
    execution_id: UUID,
) -> list[dict]:
    execution = db.get(
        ApplicationExecution,
        execution_id,
    )

    if execution is None:
        raise ValueError(
            "Application execution not found."
        )

    events = (
        db.query(ExecutionEvent)
        .filter(
            ExecutionEvent.execution_id == execution_id,
        )
        .order_by(
            ExecutionEvent.step.asc(),
            ExecutionEvent.created_at.asc(),
            ExecutionEvent.id.asc(),
        )
        .all()
    )

    return [
        _event_response(event)
        for event in events
    ]


def _event_response(
    event: ExecutionEvent,
) -> dict:
    return {
        "event_id": str(event.id),
        "execution_id": str(event.execution_id),
        "event_type": event.event_type,
        "step": event.step,
        "action": event.action,
        "details": event.details,
        "success": event.success,
        "created_at": event.created_at,
    }

