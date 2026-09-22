from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models.application import Application
from backend.app.models.application_package import ApplicationPackage
from backend.app.models.candidate import CandidateProfile
from backend.app.models.resume import Resume
from backend.app.models.user import User


def build_application_data(
    db: Session,
    application_id: UUID,
) -> dict:
    """
    Build the normalized runtime data required by the
    browser application agent.

    This service combines information from the existing
    application-related database models without creating
    a duplicate database table.
    """

    application = db.get(
        Application,
        application_id,
    )

    if application is None:
        raise ValueError(
            "Application not found."
        )

    if application.status.lower() != "approved":
        raise ValueError(
            "Application data can only be prepared "
            "for approved applications."
        )

    candidate = db.get(
        CandidateProfile,
        application.candidate_id,
    )

    if candidate is None:
        raise ValueError(
            "Candidate profile not found."
        )

    user = db.get(
        User,
        candidate.user_id,
    )

    if user is None:
        raise ValueError(
            "Candidate user not found."
        )

    package = (
        db.query(ApplicationPackage)
        .filter(
            ApplicationPackage.application_id
            == application.id,
        )
        .first()
    )

    if package is None:
        raise ValueError(
            "Application package not found."
        )

    if not package.is_valid:
        raise ValueError(
            "Application package is not valid "
            "for browser execution."
        )

    resume = (
        db.query(Resume)
        .filter(
            Resume.candidate_id
            == candidate.id,
        )
        .order_by(
            Resume.id.desc(),
        )
        .first()
    )

    return {
        "application_id": str(application.id),
        "candidate_id": str(candidate.id),
        "job_id": str(application.job_id),
        "candidate": {
            "full_name": user.full_name,
            "email": user.email,
            "headline": candidate.headline,
            "summary": candidate.summary,
            "preferred_roles": candidate.preferred_roles,
            "preferred_locations": candidate.preferred_locations,
        },
        "resume": {
            "file_name": (
                resume.file_name
                if resume is not None
                else None
            ),
            "file_path": (
                resume.file_path
                if resume is not None
                else None
            ),
            "raw_text": (
                resume.raw_text
                if resume is not None
                else None
            ),
        },
        "application_package": {
            "readiness_score": package.readiness_score,
            "tailored_summary": package.tailored_summary,
            "cover_letter": package.cover_letter,
            "key_strengths": package.key_strengths,
            "missing_requirements": package.missing_requirements,
            "application_questions": package.application_questions,
            "evidence_used": package.evidence_used,
            "unsupported_claims": package.unsupported_claims,
            "is_valid": package.is_valid,
        },
    }