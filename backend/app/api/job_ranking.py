from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.job_ranking import (
    JobRankingRequest,
    JobRankingResponse,
)
from backend.app.services.job_ranking_service import rank_jobs_for_candidate


router = APIRouter(
    prefix="/api/job-ranking",
    tags=["Job Ranking"],
)


@router.post(
    "/{candidate_id}",
    response_model=JobRankingResponse,
)
def rank_jobs_endpoint(
    candidate_id: UUID,
    request: JobRankingRequest,
    db: Session = Depends(get_db),
):
    try:
        jobs = rank_jobs_for_candidate(
            db=db,
            candidate_id=candidate_id,
            job_ids=[str(job_id) for job_id in request.job_ids],
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return {
        "candidate_id": candidate_id,
        "jobs": jobs,
    }
