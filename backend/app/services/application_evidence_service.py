from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models.candidate_evidence import CandidateEvidence


def _evidence_quality(item: CandidateEvidence) -> int:
    """
    Estimate how informative an evidence record is.

    Higher-quality evidence should be preferred when multiple records
    represent the same skill.
    """

    score = 0

    category = (item.category or "").lower()
    content = (item.content or "").lower()
    source = (item.source or "").lower()

    # Concrete projects and achievements are stronger than generic skills.
    if category == "project":
        score += 5
    elif category == "achievement":
        score += 4
    elif category == "skill":
        score += 2

    # Candidate-authored/structured evidence is generally more informative
    # than a generic resume skill extraction.
    if source == "candidate_skill":
        score += 2
    elif source == "resume":
        score += 1

    # More descriptive evidence is more useful to the application generator.
    if len(content) >= 100:
        score += 2
    elif len(content) >= 50:
        score += 1

    # Evidence demonstrating actual usage is stronger.
    usage_terms = {
        "built",
        "developed",
        "implemented",
        "used",
        "experience",
        "created",
        "deployed",
    }

    if any(term in content for term in usage_terms):
        score += 2

    return score


def select_application_evidence(
    db: Session,
    candidate_id: UUID,
    matched_requirements: list[dict],
    missing_requirements: list[str],
) -> list[dict]:
    """
    Select evidence using the evidence IDs produced by the job-fit engine.

    The job-fit engine remains the source of truth for requirement-to-
    evidence relationships. This service only filters and ranks the
    already-established evidence.
    """

    evidence_ids: list[UUID] = []

    for requirement in matched_requirements:
        if not isinstance(requirement, dict):
            continue

        for evidence_id in requirement.get("evidence_ids", []):
            try:
                parsed_id = UUID(str(evidence_id))
            except ValueError:
                continue

            if parsed_id not in evidence_ids:
                evidence_ids.append(parsed_id)

    if not evidence_ids:
        return []

    evidence_records = (
        db.query(CandidateEvidence)
        .filter(
            CandidateEvidence.candidate_id == candidate_id,
            CandidateEvidence.id.in_(evidence_ids),
        )
        .all()
    )

    evidence_by_id = {
        item.id: item
        for item in evidence_records
    }

    selected_records = []

    for evidence_id in evidence_ids:
        item = evidence_by_id.get(evidence_id)

        if item is None:
            continue

        selected_records.append(item)

    # ---------------------------------------------------------
    # Deduplicate same-category + same-title evidence.
    #
    # Keep the most informative version rather than blindly
    # deleting records from the database.
    # ---------------------------------------------------------

    best_by_key: dict[tuple[str, str], CandidateEvidence] = {}

    for item in selected_records:
        key = (
            (item.category or "").strip().lower(),
            (item.title or "").strip().lower(),
        )

        existing = best_by_key.get(key)

        if existing is None:
            best_by_key[key] = item
            continue

        if _evidence_quality(item) > _evidence_quality(existing):
            best_by_key[key] = item

    # Preserve a deterministic ordering based on evidence quality.
    final_records = sorted(
        best_by_key.values(),
        key=_evidence_quality,
        reverse=True,
    )

    return [
        {
            "evidence_id": str(item.id),
            "category": item.category,
            "title": item.title,
            "content": item.content,
            "source": item.source,
        }
        for item in final_records
    ]

