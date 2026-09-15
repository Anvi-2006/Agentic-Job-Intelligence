from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.candidate import CandidateCreate, CandidateResponse
from backend.app.services.candidate_service import create_candidate, get_candidate


router = APIRouter(
    prefix="/api/candidates",
    tags=["Candidates"],
)


@router.post(
    "",
    response_model=CandidateResponse,
    status_code=201,
)
def create_candidate_endpoint(
    candidate_data: CandidateCreate,
    db: Session = Depends(get_db),
):
    return create_candidate(db, candidate_data)


@router.get(
    "/{candidate_id}",
    response_model=CandidateResponse,
)
def get_candidate_endpoint(
    candidate_id: UUID,
    db: Session = Depends(get_db),
):
    candidate = get_candidate(db, candidate_id)

    if candidate is None:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found",
        )

    return candidate