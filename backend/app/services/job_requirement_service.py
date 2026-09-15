from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models.job_requirement import JobRequirement
from backend.app.schemas.job_requirement import JobRequirementCreate

def create_job_requirement(
    db: Session,
    requirement_data: JobRequirementCreate,
) -> JobRequirement:
    requirement = JobRequirement(
        job_id=requirement_data.job_id,
        requirement=requirement_data.requirement,
        requirement_type=requirement_data.requirement_type,
        importance=requirement_data.importance,
    )

    db.add(requirement)
    db.commit()
    db.refresh(requirement)

    return requirement


def get_job_requirement(
    db: Session,
    requirement_id: UUID,
) -> JobRequirement | None:
    return db.get(JobRequirement, requirement_id)


def get_job_requirements(
    db: Session,
    job_id: UUID,
) -> list[JobRequirement]:
    return (
        db.query(JobRequirement)
        .filter(JobRequirement.job_id == job_id)
        .all()
    )