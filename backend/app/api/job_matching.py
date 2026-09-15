from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.job_matching import JobMatchingResponse
from backend.app.services.job_matching_service import match_job_requirements


router = APIRouter(
    prefix="/api/job-matching",
    tags=["Job Matching"],
)


@router.get(
    "/{candidate_id}/{job_id}",
    response_model=JobMatchingResponse,
)
def match_candidate_to_job_endpoint(
    candidate_id: UUID,
    job_id: UUID,
    db: Session = Depends(get_db),
):
    matches = match_job_requirements(
        db=db,
        candidate_id=candidate_id,
        job_id=job_id,
    )

    return JobMatchingResponse(
        candidate_id=candidate_id,
        job_id=job_id,
        matches=matches,
    )
