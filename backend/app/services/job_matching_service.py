import re

from sqlalchemy.orm import Session

from backend.app.models.candidate_evidence import CandidateEvidence
from backend.app.models.job_requirement import JobRequirement
from backend.app.models.semantic_match_cache import SemanticMatchCache

from backend.app.services.gemini_service import (
    evaluate_semantic_requirement_matches,
)
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
    "large language models": {
    "researchmind — multi-agent ai research system",
    "introduction to generative ai",
    "generative ai",
    "llms",
    },
    "ai systems": {
        "researchmind — multi-agent ai research system",
        "sentinel-x — adversarial payment security lab",
        "atrr — agentic transaction recovery & replanning",
    },
    "machine learning": {
        "supervised & unsupervised learning",
        "researchmind — multi-agent ai research system",
    },
}


def match_job_requirements(
    db: Session,
    candidate_id,
    job_id,
) -> list[dict]:
    """
    Match candidate evidence against job requirements.

    Matching order:
    1. Exact evidence match
    2. Known partial match
    3. Gemini semantic evidence matching
    4. Missing
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
    unresolved = []

    for requirement in requirements:
        requirement_name = normalize_text(requirement.requirement)

        matched_evidence = []
        match_status = "missing"
        match_reason = ""

        for item in evidence:
            evidence_text = normalize_text(
                f"{item.title} {item.content}"
            )
            evidence_title = normalize_text(item.title)

            pattern = rf"\b{re.escape(requirement_name)}\b"

            # 1. Exact evidence match
            if re.search(pattern, evidence_title, re.IGNORECASE):
                matched_evidence.append(item)
                continue

            if item.category in {"project", "achievement"}:
                if re.search(pattern, evidence_text, re.IGNORECASE):
                    matched_evidence.append(item)

        if matched_evidence:
            match_status = "matched"
            match_reason = (
                "Direct candidate evidence supports this requirement."
            )

        else:
            # 2. Known partial match
            related_requirements = PARTIAL_MATCHES.get(
                requirement_name,
                set(),
            )

            for item in evidence:
                evidence_title = normalize_text(item.title)

                if evidence_title in related_requirements:
                    matched_evidence.append(item)

            if matched_evidence:
                match_status = "partial"
                match_reason = (
                    "Related candidate evidence supports this "
                    "requirement, but direct evidence was not found."
                )
            else:
                # 3. Defer unresolved requirement to Gemini
                unresolved.append(
                    {
                        "requirement": requirement,
                        "requirement_name": requirement_name,
                    }
                )

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

    # 3. Semantic matching for unresolved requirements
    if unresolved:
        cache = (
            db.query(SemanticMatchCache)
            .filter(
                SemanticMatchCache.candidate_id == candidate_id,
                SemanticMatchCache.job_id == job_id,
                SemanticMatchCache.matcher_version == "v1",
            )
            .first()
        )

        if cache:
            semantic_results = cache.results
        else:
            try:
                semantic_results = evaluate_semantic_requirement_matches(
                    requirements=[
                        item["requirement"].requirement
                        for item in unresolved
                    ],
                    candidate_evidence=[
                        {
                            "category": item.category,
                            "title": item.title,
                            "content": item.content,
                        }
                        for item in evidence
                    ],
                )

                db.add(
                    SemanticMatchCache(
                        candidate_id=candidate_id,
                        job_id=job_id,
                        results=semantic_results,
                        matcher_version="v1",
                    )
                )
                db.flush()

            except Exception:
                semantic_results = []

        semantic_by_requirement = {
            normalize_text(item.get("requirement", "")): item
            for item in semantic_results
        }

        for result in results:
            if result["match_status"] != "missing":
                continue

            semantic = semantic_by_requirement.get(
                normalize_text(result["requirement"])
            )

            if not semantic:
                result["reason"] = (
                    "No supporting candidate evidence was found "
                    "for this requirement."
                )
                continue

            status = semantic.get("status")

            if status not in {"matched", "partial", "missing"}:
                continue

            evidence_titles = {
                normalize_text(item.title): item
                for item in evidence
            }

            semantic_evidence = []

            for title in semantic.get("evidence_titles", []):
                item = evidence_titles.get(
                    normalize_text(title)
                )

                if item:
                    semantic_evidence.append(item)

            if status in {"matched", "partial"} and semantic_evidence:
                result["match_status"] = status
                result["matched"] = status == "matched"
                result["evidence_ids"] = [
                    str(item.id)
                    for item in semantic_evidence
                ]
                result["reason"] = semantic.get(
                    "reason",
                    "Semantic candidate evidence supports this requirement.",
                )
            else:
                result["match_status"] = "missing"
                result["matched"] = False
                result["evidence_ids"] = []
                result["reason"] = (
                    "No supporting candidate evidence was found "
                    "for this requirement."
                )

    return results