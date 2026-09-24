from __future__ import annotations

import re
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models.candidate_evidence import CandidateEvidence
from backend.app.models.job_requirement import JobRequirement
from backend.app.models.semantic_match_cache import SemanticMatchCache
from backend.app.services.gemini_service import (
    evaluate_semantic_requirement_matches,
)
from backend.app.services.semantic_search_service import (
    search_candidate_evidence_batch,
)


# ---------------------------------------------------------------------------
# Matching configuration
# ---------------------------------------------------------------------------

# Strong semantic evidence.
SEMANTIC_MATCH_THRESHOLD = 0.72

# Very strong semantic evidence is treated as a full match.
SEMANTIC_FULL_MATCH_THRESHOLD = 0.82

# Related competency evidence is intentionally weaker than an exact match.
RELATED_COMPETENCY_CONFIDENCE = 0.68


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

def normalize_text(value: str | None) -> str:
    """
    Normalize text for reliable deterministic comparison.
    """
    if not value:
        return ""

    value = value.lower().strip()

    # Normalize common separators.
    value = value.replace("&", " and ")
    value = value.replace("/", " ")
    value = value.replace("-", " ")

    # Collapse whitespace.
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def tokenize(value: str | None) -> set[str]:
    """
    Return normalized word tokens.
    """
    normalized = normalize_text(value)

    if not normalized:
        return set()

    return {
        token
        for token in re.findall(r"[a-z0-9+#.]+", normalized)
        if token
    }


# ---------------------------------------------------------------------------
# Generic competency relationships
# ---------------------------------------------------------------------------
#
# These are intentionally competency-level relationships.
#
# Do NOT put candidate-specific project names here.
#
# Example:
#
#   requirement: "problem solving"
#   evidence:    "data structures & algorithms"
#
# becomes a PARTIAL match because DSA is credible supporting evidence,
# but it does not prove that the candidate explicitly demonstrated every
# form of problem solving.
#
# The same principle applies to the other groups below.
# ---------------------------------------------------------------------------

RELATED_COMPETENCIES: dict[str, set[str]] = {
    "problem solving": {
        "data structures and algorithms",
        "data structures",
        "algorithms",
        "algorithm design",
        "competitive programming",
    },
    "data structures": {
        "data structures and algorithms",
        "algorithms",
        "algorithm design",
    },
    "algorithms": {
        "data structures and algorithms",
        "data structures",
        "algorithm design",
        "competitive programming",
    },
    "rest apis": {
        "fastapi",
        "django rest framework",
        "express",
        "express.js",
        "node.js",
        "restful apis",
        "rest api",
    },
    "rest api": {
        "fastapi",
        "django rest framework",
        "express",
        "express.js",
        "node.js",
        "restful apis",
        "rest apis",
    },
    "databases": {
        "postgresql",
        "mysql",
        "mongodb",
        "sql",
        "sqlalchemy",
    },
    "sql": {
        "postgresql",
        "mysql",
        "sqlalchemy",
    },
    "backend development": {
        "fastapi",
        "django",
        "node.js",
        "express.js",
        "express",
    },
    "web development": {
        "react",
        "react.js",
        "javascript",
        "html",
        "css",
        "node.js",
        "express.js",
    },
    "machine learning": {
        "supervised and unsupervised learning",
        "supervised learning",
        "unsupervised learning",
        "deep learning",
        "scikit learn",
        "tensorflow",
        "pytorch",
    },
    "deep learning": {
        "machine learning",
        "pytorch",
        "tensorflow",
        "neural networks",
    },
    "artificial intelligence": {
        "machine learning",
        "deep learning",
        "generative ai",
        "large language models",
        "llms",
    },
    "ai engineering": {
        "machine learning",
        "generative ai",
        "large language models",
        "llms",
        "artificial intelligence",
        "ai systems",
    },
    "large language models": {
        "llms",
        "generative ai",
        "transformers",
    },
    "llms": {
        "large language models",
        "generative ai",
    },
    "generative ai": {
        "large language models",
        "llms",
        "artificial intelligence",
    },
    "software engineering": {
        "python",
        "java",
        "javascript",
        "c++",
        "backend development",
        "web development",
    },
    "object oriented programming": {
        "oop",
        "java",
        "c++",
        "python",
    },
    "oop": {
        "object oriented programming",
        "java",
        "c++",
        "python",
    },
}


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def _normalize_requirement_variants(
    requirement: JobRequirement,
) -> list[str]:
    """
    Build normalized textual variants for a job requirement.

    The matcher uses structured requirement fields rather than relying only
    on the display name.
    """
    values = [
        getattr(requirement, "requirement", None),
        getattr(requirement, "normalized_name", None),
        getattr(requirement, "original_text", None),
        getattr(requirement, "context", None),
    ]

    variants: list[str] = []

    for value in values:
        normalized = normalize_text(value)

        if normalized and normalized not in variants:
            variants.append(normalized)

    return variants


def _evidence_text(evidence: CandidateEvidence) -> str:
    """
    Combine the strongest candidate-evidence fields for deterministic
    comparison.
    """
    return normalize_text(
        " ".join(
            [
                evidence.title or "",
                evidence.content or "",
                evidence.category or "",
            ]
        )
    )


def _requirement_name(requirement: JobRequirement) -> str:
    """
    Return the best human-readable requirement name.
    """
    return (
        getattr(requirement, "requirement", None)
        or getattr(requirement, "normalized_name", None)
        or getattr(requirement, "original_text", None)
        or ""
    ).strip()


def _normalized_requirement_name(requirement: JobRequirement) -> str:
    """
    Return the normalized requirement name used for matching.
    """
    normalized_name = getattr(requirement, "normalized_name", None)

    if normalized_name:
        return normalize_text(normalized_name)

    return normalize_text(_requirement_name(requirement))


# ---------------------------------------------------------------------------
# Deterministic matching
# ---------------------------------------------------------------------------

def _exact_match(
    requirement: JobRequirement,
    evidence: CandidateEvidence,
) -> bool:
    """
    Determine whether candidate evidence directly supports the requirement.

    We inspect title and content, while avoiding overly broad substring
    matching wherever possible.
    """
    requirement_variants = _normalize_requirement_variants(requirement)

    if not requirement_variants:
        return False

    evidence_title = normalize_text(evidence.title)
    evidence_content = normalize_text(evidence.content)

    for variant in requirement_variants:
        # Context can contain the entire job sentence. Avoid treating a
        # long context string as an exact evidence requirement.
        if len(variant.split()) > 8:
            continue

        if variant and (
            variant == evidence_title
            or variant in evidence_title
            or variant in evidence_content
        ):
            return True

    return False


def _related_competency_match(
    requirement: JobRequirement,
    evidence: CandidateEvidence,
) -> tuple[bool, str | None]:
    """
    Check whether evidence represents a known related competency.

    Returns:
        (matched, matched_competency)
    """
    requirement_name = _normalized_requirement_name(requirement)

    if not requirement_name:
        return False, None

    related_items = RELATED_COMPETENCIES.get(requirement_name, set())

    if not related_items:
        return False, None

    evidence_title = normalize_text(evidence.title)
    evidence_content = normalize_text(evidence.content)

    # Title is the strongest deterministic signal.
    for related in related_items:
        normalized_related = normalize_text(related)

        if not normalized_related:
            continue

        if normalized_related == evidence_title:
            return True, related

        if normalized_related in evidence_title:
            return True, related

    # Content is weaker, but still useful for structured evidence such as
    # projects and achievements.
    for related in related_items:
        normalized_related = normalize_text(related)

        if normalized_related and normalized_related in evidence_content:
            return True, related

    return False, None


def _token_overlap_match(
    requirement: JobRequirement,
    evidence: CandidateEvidence,
) -> bool:
    """
    Detect useful lexical overlap for multi-word requirements.

    This is deliberately conservative: at least two meaningful tokens must
    overlap for a multi-token requirement.
    """
    requirement_name = _normalized_requirement_name(requirement)

    requirement_tokens = tokenize(requirement_name)
    evidence_tokens = tokenize(
        f"{evidence.title} {evidence.content}"
    )

    if not requirement_tokens or not evidence_tokens:
        return False

    meaningful_requirement_tokens = {
        token
        for token in requirement_tokens
        if token not in {
            "and",
            "or",
            "with",
            "experience",
            "knowledge",
            "skills",
            "skill",
        }
    }

    if not meaningful_requirement_tokens:
        return False

    overlap = meaningful_requirement_tokens & evidence_tokens

    if len(meaningful_requirement_tokens) == 1:
        return len(overlap) == 1

    return len(overlap) >= 2


# ---------------------------------------------------------------------------
# Evidence lookup
# ---------------------------------------------------------------------------

def _load_candidate_evidence(
    db: Session,
    candidate_id: UUID,
) -> list[CandidateEvidence]:
    """
    Load all candidate evidence once for deterministic matching.
    """
    return (
        db.query(CandidateEvidence)
        .filter(CandidateEvidence.candidate_id == candidate_id)
        .all()
    )


# ---------------------------------------------------------------------------
# Semantic cache helpers
# ---------------------------------------------------------------------------

def _get_cached_semantic_match(
    db: Session,
    requirement: str,
    evidence_id: UUID,
) -> dict[str, Any] | None:
    """
    Read a cached Gemini semantic decision when available.

    The cache model is intentionally treated defensively because older
    database versions may not contain every optional field.
    """
    normalized_requirement = normalize_text(requirement)

    query = db.query(SemanticMatchCache)

    filters = []

    if hasattr(SemanticMatchCache, "requirement"):
        filters.append(
            SemanticMatchCache.requirement == normalized_requirement
        )

    if hasattr(SemanticMatchCache, "evidence_id"):
        filters.append(
            SemanticMatchCache.evidence_id == evidence_id
        )

    if not filters:
        return None

    item = query.filter(*filters).first()

    if item is None:
        return None

    result: dict[str, Any] = {}

    for field in (
        "matched",
        "match_status",
        "reason",
        "confidence",
    ):
        if hasattr(item, field):
            result[field] = getattr(item, field)

    return result or None


def _save_cached_semantic_match(
    db: Session,
    requirement: str,
    evidence_id: UUID,
    result: dict[str, Any],
) -> None:
    """
    Persist Gemini semantic decisions when the cache model supports them.
    """
    if not hasattr(SemanticMatchCache, "requirement"):
        return

    if not hasattr(SemanticMatchCache, "evidence_id"):
        return

    existing = (
        db.query(SemanticMatchCache)
        .filter(
            SemanticMatchCache.requirement
            == normalize_text(requirement),
            SemanticMatchCache.evidence_id == evidence_id,
        )
        .first()
    )

    if existing is not None:
        return

    payload: dict[str, Any] = {
        "requirement": normalize_text(requirement),
        "evidence_id": evidence_id,
    }

    for field in (
        "matched",
        "match_status",
        "reason",
        "confidence",
    ):
        if hasattr(SemanticMatchCache, field) and field in result:
            payload[field] = result[field]

    try:
        item = SemanticMatchCache(**payload)
        db.add(item)
        db.commit()
    except Exception:
        db.rollback()


# ---------------------------------------------------------------------------
# Gemini fallback
# ---------------------------------------------------------------------------

def _semantic_gemini_fallback(
    db: Session,
    requirement: JobRequirement,
    evidence: list[CandidateEvidence],
) -> dict[str, Any] | None:
    """
    Use Gemini only when deterministic and pgvector matching do not provide
    enough evidence.

    Gemini is instructed to reason only over supplied candidate evidence.
    """
    if not evidence:
        return None

    requirement_name = _requirement_name(requirement)

    evidence_payload = []

    for item in evidence:
        evidence_payload.append(
            {
                "evidence_id": str(item.id),
                "category": item.category,
                "title": item.title,
                "content": item.content,
            }
        )

    try:
        semantic_results = evaluate_semantic_requirement_matches(
            requirements=[
                {
                    "requirement": requirement_name,
                    "normalized_name": _normalized_requirement_name(
                        requirement
                    ),
                    "context": getattr(
                        requirement,
                        "context",
                        None,
                    ),
                }
            ],
            evidence=evidence_payload,
        )
    except Exception:
        return None

    if not semantic_results:
        return None

    # The Gemini helper may return either a list or a dictionary depending
    # on the version of the service implementation.
    if isinstance(semantic_results, dict):
        candidates = semantic_results.get(
            "matches",
            semantic_results.get("results", []),
        )
    else:
        candidates = semantic_results

    if not isinstance(candidates, list):
        return None

    normalized_requirement = _normalized_requirement_name(requirement)

    for result in candidates:
        if not isinstance(result, dict):
            continue

        returned_requirement = normalize_text(
            result.get("requirement")
            or result.get("normalized_name")
            or ""
        )

        if (
            returned_requirement
            and returned_requirement != normalized_requirement
            and returned_requirement
            != normalize_text(requirement_name)
        ):
            continue

        evidence_id = result.get("evidence_id")

        if not evidence_id:
            continue

        try:
            evidence_uuid = UUID(str(evidence_id))
        except (ValueError, TypeError):
            continue

        matched = bool(result.get("matched", False))
        confidence = float(result.get("confidence", 0.0) or 0.0)

        if not matched:
            continue

        status = result.get("match_status")

        if status not in {"matched", "partial"}:
            status = (
                "matched"
                if confidence >= 0.82
                else "partial"
            )

        return {
            "evidence_id": evidence_uuid,
            "match_status": status,
            "confidence": confidence,
            "reason": result.get(
                "reason",
                "Gemini identified supporting candidate evidence.",
            ),
            "evidence_match_type": "gemini",
        }

    return None


# ---------------------------------------------------------------------------
# Main matching function
# ---------------------------------------------------------------------------

def match_job_requirements(
    db: Session,
    candidate_id: UUID,
    job_id: UUID,
) -> list[dict]:
    """
    Match candidate evidence against job requirements.

    Matching order:

    1. Direct deterministic evidence
    2. Known related competency
    3. pgvector semantic retrieval
    4. Gemini semantic fallback

    The system intentionally distinguishes:
        matched  -> direct/strong evidence
        partial  -> credible related evidence
        missing  -> insufficient evidence

    No candidate claim is created merely because a job requirement sounds
    semantically similar to an unrelated piece of evidence.
    """

    requirements = (
        db.query(JobRequirement)
        .filter(JobRequirement.job_id == job_id)
        .order_by(JobRequirement.id)
        .all()
    )

    if not requirements:
        return []

    candidate_evidence = _load_candidate_evidence(
        db=db,
        candidate_id=candidate_id,
    )

    results: list[dict] = []

    # ------------------------------------------------------------------
    # First pass: deterministic matching
    # ------------------------------------------------------------------

    unresolved_requirements: list[JobRequirement] = []

    for requirement in requirements:
        requirement_name = _requirement_name(requirement)
        normalized_name = _normalized_requirement_name(requirement)

        matched_evidence: list[CandidateEvidence] = []

        # Exact/direct evidence.
        for evidence in candidate_evidence:
            if _exact_match(requirement, evidence):
                matched_evidence.append(evidence)

        if matched_evidence:
            results.append(
                {
                    "requirement": requirement_name,
                    "normalized_name": normalized_name,
                    "original_text": getattr(
                        requirement,
                        "original_text",
                        None,
                    ),
                    "context": getattr(
                        requirement,
                        "context",
                        None,
                    ),
                    "requirement_type": getattr(
                        requirement,
                        "requirement_type",
                        None,
                    ),
                    "category": getattr(
                        requirement,
                        "category",
                        None,
                    ),
                    "importance": requirement.importance,
                    "matched": True,
                    "match_status": "matched",
                    "evidence_ids": [
                        evidence.id
                        for evidence in matched_evidence
                    ],
                    "reason": (
                        "Direct candidate evidence supports "
                        "this requirement."
                    ),
                    "confidence": 0.95,
                    "evidence_match_type": "deterministic",
                }
            )
            continue

        # Related competency evidence.
        related_matches: list[
            tuple[CandidateEvidence, str]
        ] = []

        for evidence in candidate_evidence:
            matched, related = _related_competency_match(
                requirement,
                evidence,
            )

            if matched and related:
                related_matches.append(
                    (evidence, related)
                )

        if related_matches:
            evidence_ids = [
                evidence.id
                for evidence, _ in related_matches
            ]

            related_names = sorted(
                {
                    related
                    for _, related in related_matches
                }
            )

            results.append(
                {
                    "requirement": requirement_name,
                    "normalized_name": normalized_name,
                    "original_text": getattr(
                        requirement,
                        "original_text",
                        None,
                    ),
                    "context": getattr(
                        requirement,
                        "context",
                        None,
                    ),
                    "requirement_type": getattr(
                        requirement,
                        "requirement_type",
                        None,
                    ),
                    "category": getattr(
                        requirement,
                        "category",
                        None,
                    ),
                    "importance": requirement.importance,
                    "matched": False,
                    "match_status": "partial",
                    "evidence_ids": evidence_ids,
                    "reason": (
                        "Candidate evidence supports a related "
                        "competency: "
                        + ", ".join(related_names)
                        + "."
                    ),
                    "confidence": RELATED_COMPETENCY_CONFIDENCE,
                    "evidence_match_type": "related_competency",
                }
            )
            continue

        # Conservative lexical overlap.
        lexical_matches = [
            evidence
            for evidence in candidate_evidence
            if _token_overlap_match(requirement, evidence)
        ]

        if lexical_matches:
            results.append(
                {
                    "requirement": requirement_name,
                    "normalized_name": normalized_name,
                    "original_text": getattr(
                        requirement,
                        "original_text",
                        None,
                    ),
                    "context": getattr(
                        requirement,
                        "context",
                        None,
                    ),
                    "requirement_type": getattr(
                        requirement,
                        "requirement_type",
                        None,
                    ),
                    "category": getattr(
                        requirement,
                        "category",
                        None,
                    ),
                    "importance": requirement.importance,
                    "matched": False,
                    "match_status": "partial",
                    "evidence_ids": [
                        evidence.id
                        for evidence in lexical_matches
                    ],
                    "reason": (
                        "Candidate evidence contains overlapping "
                        "competency terms."
                    ),
                    "confidence": 0.65,
                    "evidence_match_type": "lexical",
                }
            )
            continue

        unresolved_requirements.append(requirement)

    # ------------------------------------------------------------------
    # Second pass: semantic retrieval for unresolved requirements
    # ------------------------------------------------------------------

    if unresolved_requirements:
        semantic_queries: list[str] = []

        for requirement in unresolved_requirements:
            requirement_name = _requirement_name(requirement)
            context = getattr(requirement, "context", None)

            if context:
                query = (
                    f"Requirement: {requirement_name}\n"
                    f"Job context: {context}"
                )
            else:
                query = requirement_name

            semantic_queries.append(query)

        try:
            semantic_results = search_candidate_evidence_batch(
                db=db,
                candidate_id=candidate_id,
                queries=semantic_queries,
                limit=5,
            )
        except Exception:
            semantic_results = {}

        for requirement, query in zip(
            unresolved_requirements,
            semantic_queries,
        ):
            requirement_name = _requirement_name(requirement)
            normalized_name = _normalized_requirement_name(
                requirement
            )

            candidates = semantic_results.get(
                query,
                [],
            )

            accepted_semantic_matches = []

            for candidate in candidates:
                similarity = float(
                    candidate.get("similarity", 0.0)
                    or 0.0
                )

                if similarity < SEMANTIC_MATCH_THRESHOLD:
                    continue

                accepted_semantic_matches.append(
                    (
                        candidate,
                        similarity,
                    )
                )

            if accepted_semantic_matches:
                best_candidate, similarity = max(
                    accepted_semantic_matches,
                    key=lambda item: item[1],
                )

                evidence_id = best_candidate.get(
                    "evidence_id"
                )

                if evidence_id:
                    status = (
                        "matched"
                        if similarity
                        >= SEMANTIC_FULL_MATCH_THRESHOLD
                        else "partial"
                    )

                    reason = (
                        "Strong semantic evidence supports "
                        "this requirement."
                        if status == "matched"
                        else
                        "Candidate evidence is semantically "
                        "related to this requirement."
                    )

                    results.append(
                        {
                            "requirement": requirement_name,
                            "normalized_name": normalized_name,
                            "original_text": getattr(
                                requirement,
                                "original_text",
                                None,
                            ),
                            "context": getattr(
                                requirement,
                                "context",
                                None,
                            ),
                            "requirement_type": getattr(
                                requirement,
                                "requirement_type",
                                None,
                            ),
                            "category": getattr(
                                requirement,
                                "category",
                                None,
                            ),
                            "importance": requirement.importance,
                            "matched": status == "matched",
                            "match_status": status,
                            "evidence_ids": [
                                evidence_id
                            ],
                            "reason": reason,
                            "confidence": round(
                                similarity,
                                3,
                            ),
                            "evidence_match_type": "semantic",
                        }
                    )
                    continue

            # ----------------------------------------------------------
            # Gemini fallback
            # ----------------------------------------------------------

            gemini_result = _semantic_gemini_fallback(
                db=db,
                requirement=requirement,
                evidence=candidate_evidence,
            )

            if gemini_result:
                results.append(
                    {
                        "requirement": requirement_name,
                        "normalized_name": normalized_name,
                        "original_text": getattr(
                            requirement,
                            "original_text",
                            None,
                        ),
                        "context": getattr(
                            requirement,
                            "context",
                            None,
                        ),
                        "requirement_type": getattr(
                            requirement,
                            "requirement_type",
                            None,
                        ),
                        "category": getattr(
                            requirement,
                            "category",
                            None,
                        ),
                        "importance": requirement.importance,
                        "matched": (
                            gemini_result["match_status"]
                            == "matched"
                        ),
                        "match_status": gemini_result[
                            "match_status"
                        ],
                        "evidence_ids": [
                            gemini_result["evidence_id"]
                        ],
                        "reason": gemini_result["reason"],
                        "confidence": gemini_result[
                            "confidence"
                        ],
                        "evidence_match_type": "gemini",
                    }
                )
                continue

            # ----------------------------------------------------------
            # Missing
            # ----------------------------------------------------------

            results.append(
                {
                    "requirement": requirement_name,
                    "normalized_name": normalized_name,
                    "original_text": getattr(
                        requirement,
                        "original_text",
                        None,
                    ),
                    "context": getattr(
                        requirement,
                        "context",
                        None,
                    ),
                    "requirement_type": getattr(
                        requirement,
                        "requirement_type",
                        None,
                    ),
                    "category": getattr(
                        requirement,
                        "category",
                        None,
                    ),
                    "importance": requirement.importance,
                    "matched": False,
                    "match_status": "missing",
                    "evidence_ids": [],
                    "reason": (
                        "No sufficiently relevant candidate "
                        "evidence was found."
                    ),
                    "confidence": 0.0,
                    "evidence_match_type": "none",
                }
            )

    return results

