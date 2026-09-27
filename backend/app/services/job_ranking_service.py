from sqlalchemy.orm import Session

from backend.app.models.job import Job
from backend.app.services.job_fit_service import calculate_job_fit_score


def get_recommendation_level(score: float) -> str:
    if score >= 85:
        return "strong_match"
    if score >= 70:
        return "good_match"
    if score >= 50:
        return "moderate_match"
    return "weak_match"


def build_recommendation_reason(fit: dict) -> str:
    matched = [
        match["requirement"]
        for match in fit["matches"]
        if match["match_status"] == "matched"
    ]

    partial = [
        match["requirement"]
        for match in fit["matches"]
        if match["match_status"] == "partial"
    ]

    missing = [
        match["requirement"]
        for match in fit["matches"]
        if match["match_status"] == "missing"
    ]

    parts = []

    if matched:
        parts.append(f"Strong match on {', '.join(matched)}")

    if partial:
        parts.append(f"partial match on {', '.join(partial)}")

    if missing:
        parts.append(f"missing {', '.join(missing)}")

    if not parts:
        return "No matching evidence found."

    return ", ".join(parts) + "."


def rank_jobs_for_candidate(
    db: Session,
    candidate_id,
    job_ids: list[str],
) -> list[dict]:

    if not job_ids:
        return []

    unique_job_ids = list(dict.fromkeys(job_ids))

    jobs = (
        db.query(Job)
        .filter(Job.id.in_(unique_job_ids))
        .all()
    )

    found_job_ids = {str(job.id) for job in jobs}
    missing_job_ids = [
        job_id
        for job_id in unique_job_ids
        if job_id not in found_job_ids
    ]

    if missing_job_ids:
        raise ValueError(
            f"Jobs not found: {', '.join(missing_job_ids)}"
        )

    ranked_jobs = []

    for job in jobs:
        fit = calculate_job_fit_score(
            db=db,
            candidate_id=candidate_id,
            job_id=job.id,
        )

        ranked_jobs.append(
            {
                "job_id": str(job.id),
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "job_url": job.job_url,
                "fit_score": fit["score"],
                "recommendation": get_recommendation_level(
                    fit["score"]
                ),
                "recommendation_reason": build_recommendation_reason(
                    fit
                ),
                "matched_requirements": fit["matched_requirements"],
                "total_requirements": fit["total_requirements"],
                "missing_requirements": fit["missing_requirements"],
                "partial_requirements": fit["partial_requirements"],
            }
        )

    ranked_jobs.sort(
        key=lambda job: job["fit_score"],
        reverse=True,
    )

    return ranked_jobs
