from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models.job import Job
from backend.app.models.candidate import CandidateProfile
from backend.app.models.user import User

from backend.app.services.application_evidence_service import (
    select_application_evidence,
)
from backend.app.services.application_readiness_service import (
    calculate_application_readiness,
)
from backend.app.services.evidence_validator import (
    validate_application_package,
    validate_generated_summary,
)
from backend.app.services.application_quality_validator import (
    validate_application_quality,
)
from backend.app.services.gemini_service import (
    generate_complete_application_package,
    regenerate_application_package,
)
from backend.app.services.job_fit_service import (
    calculate_job_fit_score,
)
from backend.app.services.job_understanding_service import (
    extract_job_requirements,
)


MAX_REPAIR_ATTEMPTS = 2


def _collect_validation_issues(
    validation: dict,
    package_validation: dict,
    quality_validation: dict,
) -> list[str]:
    """
    Combine all validation failures into one clean list.
    """

    issues = []

    issues.extend(
        validation.get("unsupported_claims", [])
    )

    issues.extend(
        package_validation.get("unsupported_claims", [])
    )

    issues.extend(
        quality_validation.get("quality_issues", [])
    )

    return list(dict.fromkeys(issues))


def _validate_generated_package(
    ai_package: dict,
    evidence: list[dict],
    missing_requirements: list[str],
    candidate_name: str,
) -> dict:
    """
    Validate the complete generated application package.

    The package contains the tailored summary, cover letter,
    strengths, and application questions.
    """

    tailored_summary = ai_package.get(
        "tailored_summary",
        "",
    )

    package_validation = validate_application_package(
        package=ai_package,
        candidate_evidence=evidence,
        missing_requirements=missing_requirements,
    )

    quality_validation = validate_application_quality(
        ai_package,
        candidate_name=candidate_name,
    )

    validation = validate_generated_summary(
        summary=tailored_summary,
        candidate_evidence=evidence,
        missing_requirements=missing_requirements,
    )

    issues = _collect_validation_issues(
        validation=validation,
        package_validation=package_validation,
        quality_validation=quality_validation,
    )

    return {
        "validation": validation,
        "package_validation": package_validation,
        "quality_validation": quality_validation,
        "issues": issues,
        "is_valid": (
            validation["is_valid"]
            and package_validation["is_valid"]
            and quality_validation["is_valid"]
        ),
    }


def generate_application_package(
    db: Session,
    candidate_id: UUID,
    job_id: UUID,
) -> dict:
    """
    Generate an evidence-grounded application package.

    The workflow:

    1. Calculate candidate readiness.
    2. Calculate job fit.
    3. Select supporting candidate evidence.
    4. Extract job requirements.
    5. Generate the complete application package with one Gemini call.
    6. Validate the generated package.
    7. If invalid, ask Gemini to regenerate the complete package.
    8. Validate the repaired package again.
    9. Return the final package and validation status.

    Gemini is never allowed to bypass the validation layer.
    """

    job = db.get(Job, job_id)

    if job is None:
        raise ValueError("Job not found")

    candidate = db.get(CandidateProfile, candidate_id)

    if candidate is None:
        raise ValueError("Candidate not found")

    user = db.get(User, candidate.user_id)

    if user is None:
        raise ValueError("Candidate user not found")

    candidate_name = user.full_name

    readiness = calculate_application_readiness(
        db=db,
        candidate_id=candidate_id,
        job_id=job_id,
    )

    fit = calculate_job_fit_score(
        db=db,
        candidate_id=candidate_id,
        job_id=job_id,
    )

    evidence = select_application_evidence(
        db=db,
        candidate_id=candidate_id,
        matched_requirements=fit["matches"],
        missing_requirements=fit["missing_requirements"],
    )

    requirements = extract_job_requirements(
        job.description
    )

    ai_package = generate_complete_application_package(
        job_title=job.title,
        company=job.company,
        job_requirements=requirements,
        candidate_name=candidate_name,
        job_description=job.description,
        candidate_evidence=evidence,
        matched_requirements=fit["matches"],
        missing_requirements=fit["missing_requirements"],
    )

    tailored_summary = ai_package["tailored_summary"]


    validation_result = _validate_generated_package(
        ai_package=ai_package,
        evidence=evidence,
        missing_requirements=fit["missing_requirements"],
        candidate_name=candidate_name,
    )

    # ---------------------------------------------------------
    # Repair loop
    # ---------------------------------------------------------

    repair_attempts = 0

    while (
        not validation_result["is_valid"]
        and repair_attempts < MAX_REPAIR_ATTEMPTS
    ):
        repair_attempts += 1

        try:
            ai_package = regenerate_application_package(
                job_title=job.title,
                company=job.company,
                candidate_name=candidate_name,
                job_description=job.description,
                candidate_evidence=evidence,
                matched_requirements=fit["matches"],
                missing_requirements=fit["missing_requirements"],
                tailored_summary=tailored_summary,
                previous_package=ai_package,
                validation_issues=validation_result["issues"],
            )

            tailored_summary = ai_package["tailored_summary"]

        except Exception as exc:
            validation_result["issues"].append(
                f"AI repair unavailable: {type(exc).__name__}"
            )

            break

        validation_result = _validate_generated_package(
            ai_package=ai_package,
            evidence=evidence,
            missing_requirements=fit["missing_requirements"],
            candidate_name=candidate_name,
        )


    # ---------------------------------------------------------
    # Final result
    # ---------------------------------------------------------

    cover_letter = ai_package["cover_letter"]

    return {

        "candidate_id": candidate_id,
        "job_id": job_id,
        "company": job.company,
        "job_title": job.title,
        "fit_score": fit["score"],
        "readiness_score": readiness["readiness_score"],
        "recommendation": readiness["recommendation"],
        "tailored_summary": ai_package["tailored_summary"],
        "cover_letter": cover_letter,
        "key_strengths": ai_package["key_strengths"],
        "missing_requirements": fit["missing_requirements"],
        "application_questions": ai_package[
            "application_questions"
        ],
        "evidence_used": [
            item["title"]
            for item in evidence
        ],
        "unsupported_claims": validation_result["issues"],
        "is_valid": validation_result["is_valid"],
    }
