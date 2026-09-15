from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.resume_tailoring import TailoredResumeResponse
from backend.app.services.resume_tailoring_service import (
    generate_tailored_resume,
)


router = APIRouter(
    prefix="/api/resume-tailoring",
    tags=["Resume Tailoring"],
)


@router.post(
    "/{candidate_id}/{job_id}",
    response_model=TailoredResumeResponse,
)
def generate_tailored_resume_endpoint(
    candidate_id: UUID,
    job_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        result = generate_tailored_resume(
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