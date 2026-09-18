import re

from sqlalchemy.orm import Session

from backend.app.models.candidate_evidence import CandidateEvidence
from backend.app.models.job_requirement import JobRequirement


def normalize_text(value: str) -> str:
    """
    Normalize text for reliable comparison.
    """
    return value.strip().lower()


PARTIAL_MATCHES = {
    "postgresql": {"sql", "databases"},
    "sql": {"postgresql", "mysql", "database", "databases"},
    "rest apis": {"fastapi", "django", "node.js"},
    "databases": {"sql", "postgresql", "mysql", "mongodb"},
    "problem solving": {"algorithms", "data structures", "data structures & algorithms"},
    "algorithms": {"problem solving", "data structures", "data structures & algorithms"},
    "data structures": {"algorithms", "problem solving", "data structures & algorithms"},
    "machine learning": {
        "supervised & unsupervised learning",
        "deep learning",
    },
    "deep learning": {"machine learning"},
    "large language models": {"llms", "generative ai"},
    "llms": {"large language models", "generative ai"},
    "generative ai": {"large language models", "llms"},
    "natural language processing": {"llms", "generative ai"},
    "communication": {"teamwork"},
    "teamwork": {"communication"},
}


def match_job_requirements(
    db: Session,
    candidate_id,
    job_id,
) -> list[dict]:
    """
    Match a candidate's evidence against a job's requirements.
    """

    requirements = (
        db.query(JobRequirement)
        .filter(JobRequirement.job_id == job_id)
        .all()
    )

    evidence = (
        db.query(CandidateEvidence)
        .filter(CandidateEvidence.candidate_id == candidate_id)
        .all()
    )

    results = []

    for requirement in requirements:
        requirement_name = normalize_text(requirement.requirement)

        matched_evidence = []
        match_reason = ""

        for item in evidence:
            evidence_text = normalize_text(
                f"{item.title} {item.content}"
            )
            evidence_title = normalize_text(item.title)

            pattern = rf"\b{re.escape(requirement_name)}\b"

            # Strong evidence:
            # The requirement directly matches the evidence title.
            if re.search(pattern, evidence_title, re.IGNORECASE):
                matched_evidence.append(item)
                continue

            # For project/achievement evidence, allow the requirement
            # to appear in the actual evidence content.
            if item.category in {"project", "achievement"}:
                if re.search(pattern, evidence_text, re.IGNORECASE):
                    matched_evidence.append(item)

        is_matched = len(matched_evidence) > 0

        match_status = "matched" if is_matched else "missing"

        if is_matched:
            match_reason = (
                "Direct candidate evidence supports this requirement."
            )

        if not is_matched:
            related_requirements = PARTIAL_MATCHES.get(
                requirement_name,
                set(),
            )

            for item in evidence:
                evidence_title = normalize_text(item.title)

                if evidence_title in related_requirements:
                    matched_evidence.append(item)
                    match_status = "partial"

            if match_status == "partial":
                match_reason = (
                    "Related candidate evidence supports this "
                    "requirement, but direct evidence was not found."
                )
            else:
                match_reason = (
                    "No supporting candidate evidence was found "
                    "for this requirement."
                )

        if matched_evidence and match_status != "partial":
            match_status = "matched"

        results.append(
            {
                "requirement": requirement.requirement,
                "importance": requirement.importance,
                "matched": match_status == "matched",
                "match_status": match_status,
                "evidence_ids": [
                    str(item.id)
                    for item in matched_evidence
                ],
                "reason": match_reason,
            }
        )

    return results