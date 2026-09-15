from sqlalchemy.orm import Session

from backend.app.services.job_matching_service import match_job_requirements


IMPORTANCE_WEIGHTS = {
    "required": 3,
    "preferred": 2,
    "nice_to_have": 1,
}


def calculate_job_fit_score(
    db: Session,
    candidate_id,
    job_id,
) -> dict:
    """
    Calculate a candidate's overall fit score for a job.
    """

    matches = match_job_requirements(
        db=db,
        candidate_id=candidate_id,
        job_id=job_id,
    )

    total_weight = 0
    matched_weight = 0
    score_breakdown = []

    for match in matches:
        importance = match["importance"].lower()

        weight = IMPORTANCE_WEIGHTS.get(
            importance,
            1,
        )

        total_weight += weight

        if match["match_status"] == "matched":
            contribution = weight
            matched_weight += contribution

        elif match["match_status"] == "partial":
            contribution = weight * 0.5
            matched_weight += contribution

        else:
            contribution = 0

        score_breakdown.append(
            {
                "requirement": match["requirement"],
                "importance": match["importance"],
                "match_status": match["match_status"],
                "weight": weight,
                "score_contribution": contribution,
                "reason": match["reason"],
                "evidence_ids": match["evidence_ids"],
            }
        )

    if total_weight == 0:
        score = 0
    else:
        score = round(
            (matched_weight / total_weight) * 100,
            2,
        )

    missing_requirements = [
        match["requirement"]
        for match in matches
        if match["match_status"] == "missing"
    ]

    partial_requirements = [
        match["requirement"]
        for match in matches
        if match["match_status"] == "partial"
    ]

    matched_requirements = [
        match["requirement"]
        for match in matches
        if match["match_status"] == "matched"
    ]

    if score >= 80:
        recommendation = "STRONG_MATCH"
    elif score >= 60:
        recommendation = "REVIEW"
    else:
        recommendation = "LOW_MATCH"

    return {
        "score": score,
        "recommendation": recommendation,
        "matched_requirements": len(matched_requirements),
        "total_requirements": len(matches),
        "matched_requirement_names": matched_requirements,
        "missing_requirements": missing_requirements,
        "partial_requirements": partial_requirements,
        "matched_weight": matched_weight,
        "total_weight": total_weight,
        "score_breakdown": score_breakdown,
        "matches": matches,
    }