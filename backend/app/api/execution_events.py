from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.services.execution_event_service import (
    get_execution_events,
    record_execution_event,
)


router = APIRouter(
    prefix="/api/applications",
    tags=["Execution Events"],
)


class ExecutionEventRequest(BaseModel):
    event_type: str
    step: int
    action: str
    details: str | None = None
    success: bool = True


class ExecutionEventResponse(BaseModel):
    event_id: str
    execution_id: str
    event_type: str
    step: int
    action: str
    details: str | None = None
    success: bool
    created_at: datetime | None = None


@router.post(
    "/{application_id}/execution/events",
    response_model=ExecutionEventResponse,
)
def record_execution_event_endpoint(
    application_id: UUID,
    request: ExecutionEventRequest,
    db: Session = Depends(get_db),
):
    try:
        from backend.app.services.application_execution_service import (
            _get_execution,
        )

        execution = _get_execution(
            db=db,
            application_id=application_id,
        )

        return record_execution_event(
            db=db,
            execution_id=execution.id,
            event_type=request.event_type,
            step=request.step,
            action=request.action,
            details=request.details,
            success=request.success,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.get(
    "/{application_id}/execution/events",
    response_model=list[ExecutionEventResponse],
)
def get_execution_events_endpoint(
    application_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        from backend.app.services.application_execution_service import (
            _get_execution,
        )

        execution = _get_execution(
            db=db,
            application_id=application_id,
        )

        return get_execution_events(
            db=db,
            execution_id=execution.id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )
