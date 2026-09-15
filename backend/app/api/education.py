from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.education import EducationCreate, EducationResponse
from backend.app.services.education_service import (
    create_education,
    get_education,
    get_candidate_education,
)


router = APIRouter(
    prefix="/api/education",
    tags=["Education"],
)


@router.post(
    "",
    response_model=EducationResponse,
    status_code=201,
)
def create_education_endpoint(
    education_data: EducationCreate,
    db: Session = Depends(get_db),
):
    return create_education(db, education_data)


@router.get(
    "/{education_id}",
    response_model=EducationResponse,
)
def get_education_endpoint(
    education_id: UUID,
    db: Session = Depends(get_db),
):
    education = get_education(db, education_id)

    if education is None:
        raise HTTPException(
            status_code=404,
            detail="Education record not found",
        )

    return education


@router.get(
    "/candidate/{candidate_id}",
    response_model=list[EducationResponse],
)
def get_candidate_education_endpoint(
    candidate_id: UUID,
    db: Session = Depends(get_db),
):
    return get_candidate_education(db, candidate_id)
