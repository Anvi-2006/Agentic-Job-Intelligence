from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.job import JobCreate, JobResponse
from backend.app.services.job_service import create_job, get_job, get_jobs


router = APIRouter(
    prefix="/api/jobs",
    tags=["Jobs"],
)


@router.post(
    "",
    response_model=JobResponse,
    status_code=201,
)
def create_job_endpoint(
    job_data: JobCreate,
    db: Session = Depends(get_db),
):
    return create_job(db, job_data)


@router.get(
    "",
    response_model=list[JobResponse],
)
def get_jobs_endpoint(
    db: Session = Depends(get_db),
):
    return get_jobs(db)


@router.get(
    "/{job_id}",
    response_model=JobResponse,
)
def get_job_endpoint(
    job_id: UUID,
    db: Session = Depends(get_db),
):
    job = get_job(db, job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    return job
