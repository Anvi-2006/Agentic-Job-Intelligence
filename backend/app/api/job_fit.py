from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.job_fit import JobFitResponse
from backend.app.services.job_fit_service import calculate_job_fit_score


router = APIRouter(
    prefix="/api/job-fit",
    tags=["Job Fit"],
)


@router.get(
    "/{candidate_id}/{job_id}",
    response_model=JobFitResponse,
)
def calculate_job_fit_endpoint(
    candidate_id: UUID,
    job_id: UUID,
    db: Session = Depends(get_db),
):
    result = calculate_job_fit_score(
        db=db,
        candidate_id=candidate_id,
        job_id=job_id,
    )

    return JobFitResponse(
        candidate_id=candidate_id,
        job_id=job_id,
        **result,
    )
