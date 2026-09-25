from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.job import (
    JobCreate,
    JobResponse,
    JobSearchRequest,
    JobSearchResponse,
)
from backend.app.agents.graph import search_graph
from backend.app.services.job_service import create_job, get_job, get_jobs
from backend.app.services.job_verification_service import verify_job

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


@router.post(
    "/search",
    response_model=JobSearchResponse,
)
def search_jobs_endpoint(
    request: JobSearchRequest,
):
    result = search_graph.invoke(
        {
            "candidate_id": str(request.candidate_id),
            "user_goal": request.query,
        }
    )

    if result.get("error"):
        raise HTTPException(
            status_code=400,
            detail=result["error"],
        )

    jobs = result.get("tool_result", {}).get("jobs", [])

    results = []

    for job in jobs:
        verification = verify_job(job)

        results.append(
            {
                **job,
                **verification,
            }
        )

    return {
        "candidate_id": request.candidate_id,
        "query": request.query,
        "jobs": results,
    }


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
