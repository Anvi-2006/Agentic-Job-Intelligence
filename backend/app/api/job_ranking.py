from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.services.job_ranking_service import rank_jobs_for_candidate
from backend.app.schemas.job_ranking import JobRankingResponse

router = APIRouter(
    prefix="/api/job-ranking",
    tags=["Job Ranking"],
)


@router.get(
    "/{candidate_id}",
    response_model=JobRankingResponse,
)


def rank_jobs_endpoint(
    candidate_id: UUID,
    db: Session = Depends(get_db),
):
    return {
        "candidate_id": candidate_id,
        "jobs": rank_jobs_for_candidate(
            db=db,
            candidate_id=candidate_id,
        ),
    }
