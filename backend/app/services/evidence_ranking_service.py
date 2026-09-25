from __future__ import annotations

from dataclasses import dataclass
import re


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


# Generic competency relationships.
#
# These are intentionally conservative. They represent evidence
# that can support a requirement partially, but should not be
# treated as an exact skill match.
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
        "express": 0.80,
        "restful apis": 0.80,
    },
    "problem solving": {
        "algorithms": 0.80,
        "data structures": 0.80,
        "data structures & algorithms": 0.85,
        "algorithm design": 0.80,
    },
    "machine learning": {
        "deep learning": 0.80,
        "supervised learning": 0.80,
        "unsupervised learning": 0.80,
    },
    "ai engineering": {
        "machine learning": 0.75,
        "generative ai": 0.75,
        "llms": 0.75,
        "large language models": 0.75,
    },
}


# Evidence quality reflects how directly the evidence record
# represents the candidate's capability.
#
# This is deliberately separate from requirement similarity.
# A perfect keyword match inside a generic summary should not
# outrank a dedicated skill or project record.
CATEGORY_QUALITY: dict[str, float] = {
    "skill": 1.00,
    "project": 0.95,
    "experience": 0.90,
    "achievement": 0.85,
    "certification": 0.85,
    "education": 0.75,
    "research": 0.75,
    "summary": 0.55,
    "profile": 0.50,
}


GENERIC_EVIDENCE_TITLES = {
    "professional summary",
    "summary",
    "profile",
    "about",
    "career objective",
    "objective",
}


def normalize_text(value: str | None) -> str:
    if not value:
        return ""

    value = value.lower().strip()

    # Normalize common separators so:
    # "Data Structures & Algorithms"
    # and
    # "Data Structures and Algorithms"
    # can be compared consistently.
    value = value.replace("&", " and ")

    value = re.sub(r"[^a-z0-9+#.\s-]", " ", value)
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def contains_term(text: str, term: str) -> bool:
    """
    Conservative phrase matching.

    Avoid substring errors such as:
        java -> javascript
        sql -> sqlalchemy
    """

    normalized_text = normalize_text(text)
    normalized_term = normalize_text(term)

    if not normalized_text or not normalized_term:
        return False

    pattern = rf"(?<![a-z0-9+#]){re.escape(normalized_term)}(?![a-z0-9+#])"

    return re.search(pattern, normalized_text) is not None


def evidence_quality(item: dict) -> float:
    """
    Calculate evidence-source quality independently from
    requirement similarity.
    """

    category = normalize_text(item.get("category"))

    quality = CATEGORY_QUALITY.get(category, 0.60)

    title = normalize_text(item.get("title"))

    # Generic summary/profile records are intentionally weaker.
    if title in GENERIC_EVIDENCE_TITLES:
        quality = min(quality, 0.55)

    return quality


def direct_match_score(item: dict, requirement: str) -> float | None:
    """
    Determine whether evidence directly supports a requirement.

    Priority:
        1. Exact title match
        2. Requirement phrase in a project/experience/achievement
        3. Requirement phrase in other evidence content

    Content-only matches receive a quality penalty so that a
    generic summary does not behave like dedicated evidence.
    """

    requirement_normalized = normalize_text(requirement)

    if not requirement_normalized:
        return None

    title = normalize_text(item.get("title"))
    content = normalize_text(item.get("content"))
    category = normalize_text(item.get("category"))

    quality = evidence_quality(item)

    # ---------------------------------------------------------
    # 1. Exact title match
    # ---------------------------------------------------------

    if contains_term(title, requirement_normalized):
        return 1.00 * quality

    # ---------------------------------------------------------
    # 2. Strong content match
    #
    # Projects, experience, achievements and certifications
    # provide meaningful contextual evidence.
    # ---------------------------------------------------------

    contextual_categories = {
        "project",
        "experience",
        "achievement",
        "certification",
        "research",
    }

    if category in contextual_categories:
        if contains_term(content, requirement_normalized):
            return 0.94 * quality

    # ---------------------------------------------------------
    # 3. Other evidence-content match
    #
    # Still useful, but weaker than dedicated/contextual evidence.
    # ---------------------------------------------------------

    if contains_term(content, requirement_normalized):
        return 0.75 * quality

    return None


def related_match_score(
    item: dict,
    requirement: str,
) -> tuple[float, str] | None:
    """
    Check conservative competency relationships.

    Related evidence is always weaker than direct evidence.
    """

    requirement_normalized = normalize_text(requirement)

    related_terms = RELATED_REQUIREMENTS.get(
        requirement_normalized,
        {},
    )

    if not related_terms:
        return None

    title = normalize_text(item.get("title"))
    content = normalize_text(item.get("content"))

    quality = evidence_quality(item)

    best_term: str | None = None
    best_score = 0.0

    for term, relationship_score in related_terms.items():
        normalized_term = normalize_text(term)

        # Prefer explicit evidence titles for related matches.
        if contains_term(title, normalized_term):
            score = relationship_score * quality

            if score > best_score:
                best_score = score
                best_term = term

        # Allow related competency evidence in meaningful
        # contextual records, but with a penalty.
        elif normalize_text(item.get("category")) in {
            "project",
            "experience",
            "achievement",
            "research",
        } and contains_term(content, normalized_term):
            score = relationship_score * quality * 0.90

            if score > best_score:
                best_score = score
                best_term = term

    if best_term is None:
        return None

    return best_score, best_term


def rank_evidence(
    evidence: list[dict],
    requirements: list[str],
) -> list[RankedEvidence]:
    """
    Rank candidate evidence according to both:

    1. Requirement relevance
    2. Evidence quality

    Direct evidence always outranks related evidence.

    A dedicated skill record therefore outranks a generic
    summary even when both contain the same requirement.
    """

    ranked: list[RankedEvidence] = []

    for item in evidence:
        best_match: RankedEvidence | None = None

        for requirement in requirements:

            # -------------------------------------------------
            # Direct evidence
            # -------------------------------------------------

            direct_score = direct_match_score(
                item,
                requirement,
            )

            if direct_score is not None:
                candidate = RankedEvidence(
                    evidence_id=item["evidence_id"],
                    title=item["title"],
                    content=item["content"],
                    category=item["category"],
                    source=item["source"],
                    matched_requirement=requirement,
                    match_type="direct",
                    relevance_score=round(
                        direct_score,
                        4,
                    ),
                )

                if (
                    best_match is None
                    or candidate.relevance_score
                    > best_match.relevance_score
                ):
                    best_match = candidate

                continue

            # -------------------------------------------------
            # Related competency evidence
            # -------------------------------------------------

            related_result = related_match_score(
                item,
                requirement,
            )

            if related_result is None:
                continue

            related_score, matched_term = related_result

            candidate = RankedEvidence(
                evidence_id=item["evidence_id"],
                title=item["title"],
                content=item["content"],
                category=item["category"],
                source=item["source"],
                matched_requirement=requirement,
                match_type="related",
                relevance_score=round(
                    related_score,
                    4,
                ),
            )

            if (
                best_match is None
                or candidate.relevance_score
                > best_match.relevance_score
            ):
                best_match = candidate

        if best_match is not None:
            ranked.append(best_match)

    # Highest-quality evidence first.
    ranked.sort(
        key=lambda item: (
            item.relevance_score,
            evidence_quality(
                {
                    "category": item.category,
                    "title": item.title,
                }
            ),
        ),
        reverse=True,
    )

    return ranked