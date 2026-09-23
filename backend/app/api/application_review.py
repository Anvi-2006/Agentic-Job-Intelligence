from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.services.application_review_service import (
    get_application_review,
    review_application,
)

router = APIRouter(
    prefix="/api/applications",
    tags=["Application Review"],
)


class ApplicationReviewRequest(BaseModel):
    decision: str
    reviewer_note: str | None = None


class ApplicationReviewResponse(BaseModel):
    application_id: str
    candidate_id: str
    job_id: str
    company: str
    job_title: str
    fit_score: float
    recommendation: str
    status: str
    reviewer_note: str | None = None

class ApplicationReviewDetailsResponse(BaseModel):
    application_id: str
    candidate_id: str
    job_id: str
    company: str
    job_title: str
    fit_score: float
    recommendation: str
    status: str
    reviewer_note: str | None = None
    readiness_score: float
    tailored_summary: str
    cover_letter: str
    key_strengths: list[str]
    missing_requirements: list[str]
    application_questions: list[dict]
    evidence_used: list[str]
    unsupported_claims: list[str]
    is_valid: bool

@router.get(
    "/review/{application_id}",
    response_model=ApplicationReviewDetailsResponse,
)
def get_application_review_endpoint(
    application_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        return get_application_review(
            db=db,
            application_id=application_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


@router.post(
    "/{candidate_id}/{job_id}/review",
    response_model=ApplicationReviewResponse,
)
def review_application_endpoint(
    candidate_id: UUID,
    job_id: UUID,
    request: ApplicationReviewRequest,
    db: Session = Depends(get_db),
):
    try:
        return review_application(
            db=db,
            candidate_id=candidate_id,
            job_id=job_id,
            decision=request.decision,
            reviewer_note=request.reviewer_note,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )
