from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models.application import Application
from backend.app.models.application_package import ApplicationPackage
from backend.app.models.candidate import CandidateProfile
from backend.app.models.job import Job


VALID_DECISIONS = {
    "APPROVED",
    "EDIT_REQUIRED",
    "REJECTED",
}

ALLOWED_TRANSITIONS = {
    "pending_review": {
        "approved",
        "edit_required",
        "rejected",
    },
    "edit_required": {
        "pending_review",
        "rejected",
    },
    "approved": set(),
    "rejected": set(),
}


def review_application(
    db: Session,
    candidate_id: UUID,
    job_id: UUID,
    decision: str,
    reviewer_note: str | None = None,
) -> dict:
    decision = decision.upper().strip()

    if decision not in VALID_DECISIONS:
        raise ValueError(
            "Invalid decision. Use APPROVED, EDIT_REQUIRED, or REJECTED."
        )

    candidate = db.get(CandidateProfile, candidate_id)

    if candidate is None:
        raise ValueError("Candidate not found.")

    job = db.get(Job, job_id)

    if job is None:
        raise ValueError("Job not found.")

    application = (
        db.query(Application)
        .filter(
            Application.candidate_id == candidate_id,
            Application.job_id == job_id,
        )
        .first()
    )

    if application is None:
        raise ValueError("Application not found.")

    current_status = application.status.lower()
    next_status = decision.lower()

    allowed_next_states = ALLOWED_TRANSITIONS.get(
        current_status,
        set(),
    )

    if next_status not in allowed_next_states:
        raise ValueError(
            f"Invalid application state transition: "
            f"{current_status} -> {next_status}."
        )

    # Approval is only allowed when a valid application package exists.
    if next_status == "approved":
        application_package = (
            db.query(ApplicationPackage)
            .filter(
                ApplicationPackage.application_id == application.id,
            )
            .first()
        )

        if application_package is None:
            raise ValueError(
                "Application cannot be approved without an application package."
            )

        if not application_package.is_valid:
            raise ValueError(
                "Application cannot be approved because the "
                "application package is invalid."
            )

    application.status = next_status
    application.reviewer_note = reviewer_note

    db.commit()
    db.refresh(application)

    return {
        "application_id": str(application.id),
        "candidate_id": str(candidate_id),
        "job_id": str(job_id),
        "company": job.company,
        "job_title": job.title,
        "fit_score": application.fit_score,
        "recommendation": application.recommendation,
        "status": application.status,
        "reviewer_note": application.reviewer_note,
    }

def get_application_review(
    db: Session,
    application_id: UUID,
) -> dict:
    application = db.get(Application, application_id)

    if application is None:
        raise ValueError("Application not found.")

    job = db.get(Job, application.job_id)

    if job is None:
        raise ValueError("Job not found.")

    candidate = db.get(CandidateProfile, application.candidate_id)

    if candidate is None:
        raise ValueError("Candidate not found.")

    application_package = (
        db.query(ApplicationPackage)
        .filter(
            ApplicationPackage.application_id == application.id,
        )
        .first()
    )

    if application_package is None:
        raise ValueError("Application package not found.")

    return {
        "application_id": str(application.id),
        "candidate_id": str(application.candidate_id),
        "job_id": str(application.job_id),
        "company": job.company,
        "job_title": job.title,
        "fit_score": application.fit_score,
        "recommendation": application.recommendation,
        "status": application.status,
        "reviewer_note": application.reviewer_note,
        "readiness_score": application_package.readiness_score,
        "tailored_summary": application_package.tailored_summary,
        "cover_letter": application_package.cover_letter,
        "key_strengths": application_package.key_strengths,
        "missing_requirements": application_package.missing_requirements,
        "application_questions": application_package.application_questions,
        "evidence_used": application_package.evidence_used,
        "unsupported_claims": application_package.unsupported_claims,
        "is_valid": application_package.is_valid,
    }
