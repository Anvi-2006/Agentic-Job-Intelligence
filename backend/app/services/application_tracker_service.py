from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models.application import Application
from backend.app.models.job import Job


def get_candidate_applications(
    db: Session,
    candidate_id: UUID,
):
    applications = (
        db.query(Application, Job)
        .join(Job, Application.job_id == Job.id)
        .filter(Application.candidate_id == candidate_id)
        .order_by(Application.updated_at.desc())
        .all()
    )

    results = []

    for application, job in applications:
        results.append(
            {
                "application_id": str(application.id),
                "job_id": str(application.job_id),
                "company": job.company,
                "job_title": job.title,
                "location": job.location,
                "job_url": job.job_url,
                "fit_score": application.fit_score,
                "recommendation": application.recommendation,
                "status": application.status,
                "reviewer_note": application.reviewer_note,
                "created_at": application.created_at,
                "updated_at": application.updated_at,
            }
        )

    return results