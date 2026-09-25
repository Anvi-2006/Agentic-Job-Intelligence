from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.job_intelligence import JobIntelligenceResponse
from backend.app.services.job_intelligence_service import get_job_intelligence


router = APIRouter(
    prefix="/api/job-intelligence",
    tags=["Job Intelligence"],
)


@router.get(
    "/{candidate_id}/{job_id}",
    response_model=JobIntelligenceResponse,
)
def get_job_intelligence_endpoint(
    candidate_id: UUID,
    job_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        return get_job_intelligence(
            db=db,
            candidate_id=candidate_id,
            job_id=job_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc