from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models.job import Job
from backend.app.schemas.job import JobCreate


def create_job(
    db: Session,
    job_data: JobCreate,
) -> Job:
    job = Job(
        external_id=job_data.external_id,
        title=job_data.title,
        company=job_data.company,
        location=job_data.location,
        description=job_data.description,
        source=job_data.source,
        job_url=job_data.job_url,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return job


def get_job(
    db: Session,
    job_id: UUID,
) -> Job | None:
    return db.get(Job, job_id)


def get_jobs(
    db: Session,
) -> list[Job]:
    return (
        db.query(Job)
        .order_by(Job.company, Job.title)
        .all()
    )
    
def upsert_external_job(
    db: Session,
    job_data: dict,
) -> Job:
    existing = (
        db.query(Job)
        .filter(
            Job.source == job_data["source"],
            Job.external_id == job_data["external_id"],
        )
        .first()
    )

    if existing:
        for field in (
            "title",
            "company",
            "location",
            "description",
            "job_url",
        ):
            setattr(existing, field, job_data.get(field))

        db.commit()
        db.refresh(existing)
        return existing

    job = Job(**job_data)
    db.add(job)
    db.commit()
    db.refresh(job)

    return job
