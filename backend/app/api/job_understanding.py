from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.job_understanding import (
    JobRequirementUnderstanding,
    JobUnderstandingResponse,
)
from backend.app.services.job_service import get_job
from backend.app.services.job_understanding_service import (
    understand_job_requirements,
    save_job_requirements,
)


router = APIRouter(
    prefix="/api/job-understanding",
    tags=["Job Understanding"],
)


@router.get(
    "/{job_id}",
    response_model=JobUnderstandingResponse,
)
def understand_job_endpoint(
    job_id: UUID,
    db: Session = Depends(get_db),
):
    job = get_job(db, job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    requirements = understand_job_requirements(
        job.description
    )

    saved_requirements = save_job_requirements(
        db=db,
        job_id=job.id,
        requirements=requirements,
    )

    return JobUnderstandingResponse(
        job_id=job.id,
        requirements=[
            JobRequirementUnderstanding(
                requirement=item.requirement,
                normalized_name=item.normalized_name,
                original_text=item.original_text,
                context=item.context,
                requirement_type=item.requirement_type,
                category=item.category,
                importance=item.importance,
                confidence=item.confidence,
                source=item.source,
            )
            for item in saved_requirements
        ],
        total_requirements=len(
            saved_requirements
        ),
    )