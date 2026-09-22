from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.services.application_execution_service import (
    approve_application_submission,
    create_application_execution,
    get_application_execution,
    mark_execution_failed,
    mark_execution_needs_human,
    mark_execution_submitted,
    request_submission_approval,
    resume_application_execution,
    retry_failed_execution,
    start_application_execution,
    update_execution_step,
)

from backend.app.services.application_browser_execution_service import (
    execute_application_browser_step,
)

router = APIRouter(
    prefix="/api/applications",
    tags=["Application Execution"],
)


class HumanInterventionRequest(BaseModel):
    current_action: str


class ExecutionFailureRequest(BaseModel):
    failure_reason: str

class ExecutionStepRequest(BaseModel):
    current_step: int
    current_action: str

class ApplicationExecutionResponse(BaseModel):
    execution_id: str
    application_id: str
    status: str
    current_step: int
    current_action: str | None = None
    submission_approved: bool = False
    failure_reason: str | None = None
    started_at: object | None = None
    completed_at: object | None = None
    created_at: object | None = None
    updated_at: object | None = None


@router.post(
    "/{application_id}/execution",
    response_model=ApplicationExecutionResponse,
)
def create_execution_endpoint(
    application_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        return create_application_execution(
            db=db,
            application_id=application_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.get(
    "/{application_id}/execution",
    response_model=ApplicationExecutionResponse,
)
def get_execution_endpoint(
    application_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        return get_application_execution(
            db=db,
            application_id=application_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


@router.post(
    "/{application_id}/execution/start",
    response_model=ApplicationExecutionResponse,
)
def start_execution_endpoint(
    application_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        return start_application_execution(
            db=db,
            application_id=application_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

@router.post(
    "/{application_id}/execution/request-submission-approval",
    response_model=ApplicationExecutionResponse,
)
def request_submission_approval_endpoint(
    application_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        return request_submission_approval(
            db=db,
            application_id=application_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

@router.post(
    "/{application_id}/execution/approve-submission",
    response_model=ApplicationExecutionResponse,
)
def approve_submission_endpoint(
    application_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        return approve_application_submission(
            db=db,
            application_id=application_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

@router.post(
    "/{application_id}/execution/submitted",
    response_model=ApplicationExecutionResponse,
)
def mark_submitted_endpoint(
    application_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        return mark_execution_submitted(
            db=db,
            application_id=application_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.post(
    "/{application_id}/execution/needs-human",
    response_model=ApplicationExecutionResponse,
)
def mark_needs_human_endpoint(
    application_id: UUID,
    request: HumanInterventionRequest,
    db: Session = Depends(get_db),
):
    try:
        return mark_execution_needs_human(
            db=db,
            application_id=application_id,
            current_action=request.current_action,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.post(
    "/{application_id}/execution/failed",
    response_model=ApplicationExecutionResponse,
)
def mark_failed_endpoint(
    application_id: UUID,
    request: ExecutionFailureRequest,
    db: Session = Depends(get_db),
):
    try:
        return mark_execution_failed(
            db=db,
            application_id=application_id,
            failure_reason=request.failure_reason,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

@router.post(
    "/{application_id}/execution/resume",
    response_model=ApplicationExecutionResponse,
)
def resume_execution_endpoint(
    application_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        return resume_application_execution(
            db=db,
            application_id=application_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.post(
    "/{application_id}/execution/retry",
    response_model=ApplicationExecutionResponse,
)
def retry_execution_endpoint(
    application_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        return retry_failed_execution(
            db=db,
            application_id=application_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.post(
    "/{application_id}/execution/step",
    response_model=ApplicationExecutionResponse,
)
def update_execution_step_endpoint(
    application_id: UUID,
    request: ExecutionStepRequest,
    db: Session = Depends(get_db),
):
    try:
        return update_execution_step(
            db=db,
            application_id=application_id,
            current_step=request.current_step,
            current_action=request.current_action,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

class BrowserExecutionRequest(BaseModel):
    application_url: str
    headless: bool = True


@router.post(
    "/{application_id}/execution/browser",
)
def execute_browser_endpoint(
    application_id: UUID,
    request: BrowserExecutionRequest,
):
    try:
        return execute_application_browser_step(
            application_id=application_id,
            application_url=request.application_url,
            headless=request.headless,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )