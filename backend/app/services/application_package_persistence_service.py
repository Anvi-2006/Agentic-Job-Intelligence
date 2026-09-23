from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models.application import Application
from backend.app.models.application_package import ApplicationPackage


def save_application_package(
    db: Session,
    candidate_id: UUID,
    job_id: UUID,
    package: dict,
    agent_decision: str,
) -> ApplicationPackage:
    """
    Create or update the Application and its generated ApplicationPackage.

    The application starts in pending_review so that a human can
    approve, edit, or reject it before any application action occurs.
    """

    application = (
        db.query(Application)
        .filter(
            Application.candidate_id == candidate_id,
            Application.job_id == job_id,
        )
        .first()
    )

    if application is None:
        application = Application(
            candidate_id=candidate_id,
            job_id=job_id,
            fit_score=package["fit_score"],
            recommendation=package["recommendation"],
            status="pending_review",
        )
        db.add(application)
        db.flush()
    else:
        application.fit_score = package["fit_score"]
        application.recommendation = package["recommendation"]
        if application.status not in {
            "approved",
            "rejected",
            "edit_required",
        }:
            application.status = "pending_review"

    application_package = (
        db.query(ApplicationPackage)
        .filter(
            ApplicationPackage.application_id == application.id,
        )
        .first()
    )

    if application_package is None:
        application_package = ApplicationPackage(
            application_id=application.id,
            readiness_score=package["readiness_score"],
            tailored_summary=package["tailored_summary"],
            cover_letter=package["cover_letter"],
            key_strengths=package["key_strengths"],
            missing_requirements=package["missing_requirements"],
            application_questions=package["application_questions"],
            evidence_used=package["evidence_used"],
            unsupported_claims=package["unsupported_claims"],
            is_valid=package["is_valid"],
        )
        db.add(application_package)
    else:
        application_package.readiness_score = package["readiness_score"]
        application_package.tailored_summary = package["tailored_summary"]
        application_package.cover_letter = package["cover_letter"]
        application_package.key_strengths = package["key_strengths"]
        application_package.missing_requirements = package["missing_requirements"]
        application_package.application_questions = package["application_questions"]
        application_package.evidence_used = package["evidence_used"]
        application_package.unsupported_claims = package["unsupported_claims"]
        application_package.is_valid = package["is_valid"]

    db.commit()
    db.refresh(application_package)

    return application_package
