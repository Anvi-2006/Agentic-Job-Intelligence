from typing import Literal


Decision = Literal["apply", "review", "skip"]


def decide_application(
    fit_score: float,
    missing_requirements: list[str],
    partial_requirements: list[str],
) -> dict:
    """
    Decide whether a candidate should apply, review, or skip a job.

    The decision is based on fit score and requirement gaps.
    """

    missing_count = len(missing_requirements)
    partial_count = len(partial_requirements)

    if fit_score >= 75 and missing_count == 0:
        decision: Decision = "apply"
        reason = (
            f"Strong fit at {fit_score}%. "
            "The candidate has evidence for all required requirements."
        )

    elif fit_score >= 60 and missing_count <= 1:
        decision = "review"
        reason = (
            f"Fit score is {fit_score}%, but the candidate has "
            f"{missing_count} missing and {partial_count} partial "
            "requirements. Human review is recommended before applying."
        )

    else:
        decision = "skip"
        reason = (
            f"Weak fit at {fit_score}%. "
            f"There are {missing_count} missing requirements."
        )

    return {
        "decision": decision,
        "reason": reason,
        "fit_score": fit_score,
        "missing_requirements": missing_requirements,
        "partial_requirements": partial_requirements,
    }