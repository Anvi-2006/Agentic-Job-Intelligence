from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.resume import ResumeCreate, ResumeResponse
from backend.app.services.resume_service import (
    create_resume,
    get_resume,
    get_candidate_resumes,
)


router = APIRouter(
    prefix="/api/resumes",
    tags=["Resumes"],
)


@router.post(
    "",
    response_model=ResumeResponse,
    status_code=201,
)
def create_resume_endpoint(
    resume_data: ResumeCreate,
    db: Session = Depends(get_db),
):
    return create_resume(db, resume_data)


@router.get(
    "/candidate/{candidate_id}",
    response_model=list[ResumeResponse],
)
def get_candidate_resumes_endpoint(
    candidate_id: UUID,
    db: Session = Depends(get_db),
):
    return get_candidate_resumes(db, candidate_id)


@router.get(
    "/{resume_id}",
    response_model=ResumeResponse,
)
def get_resume_endpoint(
    resume_id: UUID,
    db: Session = Depends(get_db),
):
    resume = get_resume(db, resume_id)

    if resume is None:
        raise HTTPException(
            status_code=404,
            detail="Resume not found",
        )

    return resume
