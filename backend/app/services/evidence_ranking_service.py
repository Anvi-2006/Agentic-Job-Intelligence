from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RankedEvidence:
    evidence_id: str
    title: str
    content: str
    category: str
    source: str
    matched_requirement: str
    match_type: str
    relevance_score: float


RELATED_REQUIREMENTS: dict[str, dict[str, float]] = {
    "databases": {
        "postgresql": 0.80,
        "mysql": 0.80,
        "mongodb": 0.80,
        "sql": 0.80,
        "sqlalchemy": 0.70,
    },
    "rest apis": {
        "fastapi": 0.80,
        "django": 0.80,
        "node.js": 0.80,
    },
    "problem solving": {
        "algorithms": 0.80,
        "data structures": 0.80,
    },
}


def rank_evidence(
    evidence: list[dict],
    requirements: list[str],
) -> list[RankedEvidence]:
    """
    Rank candidate evidence according to how strongly
    each item supports a specific job requirement.
    """

    ranked: list[RankedEvidence] = []

    for item in evidence:
        title = item["title"].lower().strip()

        best_match: RankedEvidence | None = None

        for requirement in requirements:
            requirement_normalized = (
                requirement.lower().strip()
            )

            # Direct evidence match.
            if requirement_normalized in title:
                candidate = RankedEvidence(
                    evidence_id=item["evidence_id"],
                    title=item["title"],
                    content=item["content"],
                    category=item["category"],
                    source=item["source"],
                    matched_requirement=requirement,
                    match_type="direct",
                    relevance_score=1.0,
                )

            # Related evidence match.
            else:
                related_terms = RELATED_REQUIREMENTS.get(
                    requirement_normalized,
                    {},
                )

                matched_term = next(
                    (
                        term
                        for term in related_terms
                        if title == term
                        or title.endswith(f" {term}")
                        or title.startswith(f"{term} ")
                    ),
                    None,
                )

                if matched_term is None:
                    continue

                candidate = RankedEvidence(
                    evidence_id=item["evidence_id"],
                    title=item["title"],
                    content=item["content"],
                    category=item["category"],
                    source=item["source"],
                    matched_requirement=requirement,
                    match_type="related",
                    relevance_score=related_terms[
                        matched_term
                    ],
                )

            if (
                best_match is None
                or candidate.relevance_score
                > best_match.relevance_score
            ):
                best_match = candidate

        if best_match is not None:
            ranked.append(best_match)

    ranked.sort(
        key=lambda item: item.relevance_score,
        reverse=True,
    )

    return ranked