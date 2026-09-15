from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.services.evidence_ranking_service import rank_evidence
from backend.app.services.semantic_search_service import (
    search_candidate_evidence_batch,
)


DETERMINISTIC_WEIGHT = 0.60
SEMANTIC_WEIGHT = 0.40


def hybrid_rank_evidence(
    db: Session,
    candidate_id: UUID,
    evidence: list[dict],
    requirements: list[str],
    semantic_limit: int = 10,
) -> list[dict]:
    """
    Combine deterministic evidence matching with
    semantic similarity from pgvector.

    Query embeddings for all requirements are generated
    in a single Gemini embedding request.
    """

    if not requirements:
        return []

    if not evidence:
        return []

    deterministic_results = rank_evidence(
        evidence=evidence,
        requirements=requirements,
    )

    deterministic_by_id = {
        item.evidence_id: item
        for item in deterministic_results
    }

    semantic_results_by_requirement = (
        search_candidate_evidence_batch(
            db=db,
            candidate_id=candidate_id,
            queries=requirements,
            limit=semantic_limit,
        )
    )

    semantic_by_id: dict[str, float] = {}

    for semantic_results in (
        semantic_results_by_requirement.values()
    ):
        for result in semantic_results:
            evidence_id = str(result["evidence_id"])
            similarity = result["similarity"]

            current = semantic_by_id.get(
                evidence_id,
                0.0,
            )

            if similarity > current:
                semantic_by_id[evidence_id] = similarity

    hybrid_results: list[dict] = []

    for item in evidence:
        evidence_id = str(item["evidence_id"])

        deterministic = deterministic_by_id.get(
            evidence_id
        )

        # Deterministic matching remains the
        # eligibility gate for resume evidence.
        if deterministic is None:
            continue

        deterministic_score = (
            deterministic.relevance_score
        )

        semantic_score = semantic_by_id.get(
            evidence_id,
            0.0,
        )

        hybrid_score = (
            DETERMINISTIC_WEIGHT
            * deterministic_score
            + SEMANTIC_WEIGHT
            * semantic_score
        )

        hybrid_results.append(
            {
                "evidence_id": item["evidence_id"],
                "title": item["title"],
                "content": item["content"],
                "category": item["category"],
                "source": item["source"],
                "matched_requirement": (
                    deterministic.matched_requirement
                ),
                "match_type": deterministic.match_type,
                "deterministic_score": (
                    deterministic_score
                ),
                "semantic_score": semantic_score,
                "hybrid_score": hybrid_score,
            }
        )

    hybrid_results.sort(
        key=lambda item: item["hybrid_score"],
        reverse=True,
    )  

    return hybrid_results