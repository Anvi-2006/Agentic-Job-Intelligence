from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.services.job_fit_service import calculate_job_fit_score
from backend.app.services.job_requirement_service import get_job_requirements
from backend.app.services.job_service import get_job
from backend.app.services.job_verification_service import verify_job


def get_job_intelligence(
    db: Session,
    candidate_id: UUID,
    job_id: UUID,
) -> dict:
    """
    Build the unified intelligence view for a candidate-job pair.

    This service orchestrates existing domain services.
    It does not duplicate matching or scoring logic.
    """

    job = get_job(
        db=db,
        job_id=job_id,
    )

    if job is None:
        raise ValueError("Job not found.")

    requirements = get_job_requirements(
        db=db,
        job_id=job_id,
    )

    verification = verify_job(
        {
            "source": job.source,
            "job_url": job.job_url,
            "company": job.company,
        }
    )

    fit = calculate_job_fit_score(
        db=db,
        candidate_id=candidate_id,
        job_id=job_id,
    )

    # The matching engine already contains the authoritative
    # requirement-level intelligence. Index it by normalized name
    # so we can enrich the persisted JobRequirement records without
    # duplicating matching logic.
    matches_by_name = {
        (match.get("normalized_name") or "").strip().lower(): match
        for match in fit.get("matches", [])
    }

    intelligence_requirements = []

    for requirement in requirements:
        normalized_name = (
            requirement.normalized_name
            or requirement.requirement
        ).strip().lower()

        match = matches_by_name.get(normalized_name)

        if match is None:
            # Defensive fallback for older requirement records or
            # unexpected matching output.
            intelligence_requirements.append(
                {
                    "id": requirement.id,
                    "requirement": requirement.requirement,
                    "normalized_name": normalized_name,
                    "original_text": (
                        requirement.original_text
                        or requirement.requirement
                    ),
                    "context": (
                        requirement.context
                        or requirement.requirement
                    ),
                    "requirement_type": requirement.requirement_type,
                    "category": requirement.category,
                    "importance": requirement.importance,
                    "match_status": "missing",
                    "matched": False,
                    "confidence": 0.0,
                    "reason": "No candidate evidence supports this requirement.",
                    "evidence_match_type": None,
                    "evidence_ids": [],
                }
            )
            continue

        intelligence_requirements.append(
            {
                "id": requirement.id,
                "requirement": requirement.requirement,
                "normalized_name": (
                    match.get("normalized_name")
                    or normalized_name
                ),
                "original_text": (
                    match.get("original_text")
                    or requirement.original_text
                    or requirement.requirement
                ),
                "context": (
                    match.get("context")
                    or requirement.context
                    or requirement.requirement
                ),
                "requirement_type": (
                    match.get("requirement_type")
                    or requirement.requirement_type
                ),
                "category": (
                    match.get("category")
                    or requirement.category
                ),
                "importance": (
                    match.get("importance")
                    or requirement.importance
                ),
                "match_status": (
                    match.get("match_status")
                    or (
                        "matched"
                        if match.get("matched")
                        else "missing"
                    )
                ),
                "matched": bool(match.get("matched")),
                "confidence": float(
                    match.get("confidence") or 0.0
                ),
                "reason": (
                    match.get("reason")
                    or "No candidate evidence supports this requirement."
                ),
                "evidence_match_type": match.get(
                    "evidence_match_type"
                ),
                "evidence_ids": match.get(
                    "evidence_ids",
                    [],
                ),
            }
        )

    skill_gaps = [
        {
            "requirement": requirement,
            "status": "missing",
        }
        for requirement in fit["missing_requirements"]
    ]

    skill_gaps.extend(
        {
            "requirement": requirement,
            "status": "partial",
        }
        for requirement in fit["partial_requirements"]
    )

    return {
        "candidate_id": candidate_id,
        "job_id": job_id,
        "job": {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "description": job.description,
            "source": job.source,
            "job_url": job.job_url,
        },
        "verification": verification,
        "requirements": intelligence_requirements,
        "fit": fit,
        "skill_gaps": skill_gaps,
    }