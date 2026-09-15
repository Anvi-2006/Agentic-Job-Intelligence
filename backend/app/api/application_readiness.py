from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.application_preparation import (
    ApplicationReadinessResponse,
)
from backend.app.services.application_readiness_service import (
    calculate_application_readiness,
)


router = APIRouter(
    prefix="/api/application-readiness",
    tags=["Application Readiness"],
)


@router.get(
    "/{candidate_id}/{job_id}",
    response_model=ApplicationReadinessResponse,
)
def get_application_readiness(
    candidate_id: UUID,
    job_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        result = calculate_application_readiness(
            db=db,
            candidate_id=candidate_id,
            job_id=job_id,
        )

        return result

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
