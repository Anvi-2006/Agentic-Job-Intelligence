from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.job_requirement import (
    JobRequirementCreate,
    JobRequirementResponse,
)
from backend.app.services.job_requirement_service import (
    create_job_requirement,
    get_job_requirement,
    get_job_requirements,
)


router = APIRouter(
    prefix="/api/job-requirements",
    tags=["Job Requirements"],
)


@router.post(
    "",
    response_model=JobRequirementResponse,
    status_code=201,
)
def create_job_requirement_endpoint(
    requirement_data: JobRequirementCreate,
    db: Session = Depends(get_db),
):
    return create_job_requirement(db, requirement_data)


@router.get(
    "/job/{job_id}",
    response_model=list[JobRequirementResponse],
)
def get_job_requirements_endpoint(
    job_id: UUID,
    db: Session = Depends(get_db),
):
    return get_job_requirements(db, job_id)


@router.get(
    "/{requirement_id}",
    response_model=JobRequirementResponse,
)
def get_job_requirement_endpoint(
    requirement_id: UUID,
    db: Session = Depends(get_db),
):
    requirement = get_job_requirement(db, requirement_id)

    if requirement is None:
        raise HTTPException(
            status_code=404,
            detail="Job requirement not found",
        )

    return requirement
