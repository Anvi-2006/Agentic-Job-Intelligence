from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models.application import Application
from backend.app.models.application_package import ApplicationPackage
from backend.app.models.job import Job
from backend.app.models.candidate import CandidateProfile


def get_saved_application_package(
    db: Session,
    candidate_id: UUID,
    job_id: UUID,
) -> dict:
    """
    Retrieve the already-generated application package.

    This function is read-only. It never calls Gemini,
    resume tailoring, matching, or package generation.
    """

    candidate = db.get(CandidateProfile, candidate_id)

    if candidate is None:
        raise ValueError("Candidate not found")

    job = db.get(Job, job_id)

    if job is None:
        raise ValueError("Job not found")

    application = (
        db.query(Application)
        .filter(
            Application.candidate_id == candidate_id,
            Application.job_id == job_id,
        )
        .first()
    )

    if application is None:
        raise ValueError("Application not found")

    package = (
        db.query(ApplicationPackage)
        .filter(
            ApplicationPackage.application_id == application.id,
        )
        .first()
    )

    if package is None:
        raise ValueError("Application package not found")

    return {
        "application_id": application.id,
        "candidate_id": candidate_id,
        "job_id": job_id,
        "company": job.company,
        "job_title": job.title,
        "readiness_score": package.readiness_score,
        "recommendation": application.recommendation,
        "tailored_summary": package.tailored_summary,
        "cover_letter": package.cover_letter,
        "key_strengths": package.key_strengths,
        "missing_requirements": package.missing_requirements,
        "application_questions": package.application_questions,
        "evidence_used": package.evidence_used,
        "unsupported_claims": package.unsupported_claims,
        "is_valid": package.is_valid,
    }