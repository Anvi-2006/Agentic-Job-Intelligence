from sqlalchemy.orm import Session

from backend.app.models.job import Job
from backend.app.services.application_evidence_service import (
    select_application_evidence,
)
from backend.app.services.evidence_validator import (
    validate_generated_summary,
)
from backend.app.services.gemini_service import (
    generate_resume_tailoring,
)
from backend.app.services.job_fit_service import (
    calculate_job_fit_score,
)
from backend.app.services.job_understanding_service import (
    extract_job_requirements,
)


def generate_tailored_resume(
    db: Session,
    candidate_id,
    job_id,
) -> dict:
    job = db.get(Job, job_id)

    if job is None:
        raise ValueError("Job not found")

    fit = calculate_job_fit_score(
        db=db,
        candidate_id=candidate_id,
        job_id=job_id,
    )

    requirements = extract_job_requirements(
        job.description
    )

    # ---------------------------------------------------------
    # Use the same evidence boundary as the application package.
    #
    # Job-fit engine determines which evidence supports which
    # requirements. The application evidence selector then
    # filters and deduplicates those records.
    # ---------------------------------------------------------

    evidence = select_application_evidence(
        db=db,
        candidate_id=candidate_id,
        matched_requirements=fit["matches"],
        missing_requirements=fit["missing_requirements"],
    )

    summary = generate_resume_tailoring(
        job_title=job.title,
        company=job.company,
        job_requirements=requirements,
        candidate_evidence=evidence,
        missing_requirements=fit["missing_requirements"],
    )

    validation = validate_generated_summary(
        summary=summary,
        candidate_evidence=evidence,
        missing_requirements=fit["missing_requirements"],
    )

    return {
        "candidate_id": candidate_id,
        "job_id": job_id,
        "summary": summary,
        "fit_score": fit["score"],
        "missing_requirements": fit["missing_requirements"],
        "partial_requirements": fit["partial_requirements"],
        "evidence_used": [
            {
                "evidence_id": item["evidence_id"],
                "title": item["title"],
            }
            for item in evidence
        ],
        "unsupported_claims": validation[
            "unsupported_claims"
        ],
        "is_valid": validation["is_valid"],
    }