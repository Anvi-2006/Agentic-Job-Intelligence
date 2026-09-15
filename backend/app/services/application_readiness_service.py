from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models.candidate_evidence import CandidateEvidence
from backend.app.services.job_fit_service import calculate_job_fit_score


def calculate_application_readiness(
    db: Session,
    candidate_id: UUID,
    job_id: UUID,
) -> dict:
    """
    Calculate whether a candidate is ready to prepare an application
    for a specific job.
    """

    fit = calculate_job_fit_score(
        db=db,
        candidate_id=candidate_id,
        job_id=job_id,
    )

    evidence_count = (
        db.query(CandidateEvidence)
        .filter(
            CandidateEvidence.candidate_id == candidate_id
        )
        .count()
    )

    matched_count = fit["matched_requirements"]
    total_requirements = fit["total_requirements"]

    missing_requirements = fit["missing_requirements"]
    partial_requirements = fit["partial_requirements"]

    if total_requirements == 0:
        readiness_score = 0.0
    else:
        readiness_score = fit["score"]

        # Verified candidate evidence improves application readiness.
        if evidence_count >= 5:
            readiness_score += 5

        # Missing requirements reduce readiness.
        readiness_score -= len(missing_requirements) * 3

        readiness_score = max(
            0.0,
            min(100.0, readiness_score),
        )

    if readiness_score >= 80:
        readiness_level = "high"
        recommendation = "APPLY"

    elif readiness_score >= 60:
        readiness_level = "review"
        recommendation = "REVIEW"

    else:
        readiness_level = "low"
        recommendation = "SKIP"

    reasons = []

    if matched_count > 0:
        reasons.append(
            f"Strong evidence for {matched_count} "
            f"of {total_requirements} job requirements"
        )

    if partial_requirements:
        reasons.append(
            "Partial evidence for "
            + ", ".join(partial_requirements)
        )

    if missing_requirements:
        reasons.append(
            "Missing evidence for "
            + ", ".join(missing_requirements)
        )

    if evidence_count >= 5:
        reasons.append(
            "Candidate has sufficient verified evidence "
            "for application preparation"
        )
    elif evidence_count > 0:
        reasons.append(
            "Candidate evidence exists but is limited"
        )
    else:
        reasons.append(
            "No verified candidate evidence is available"
        )

    return {
        "candidate_id": candidate_id,
        "job_id": job_id,
        "fit_score": fit["score"],
        "readiness_score": readiness_score,
        "readiness_level": readiness_level,
        "matched_requirements": matched_count,
        "partial_requirements": partial_requirements,
        "missing_requirements": missing_requirements,
        "evidence_count": evidence_count,
        "recommendation": recommendation,
        "reasons": reasons,
    }
