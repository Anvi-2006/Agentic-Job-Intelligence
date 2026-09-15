from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models.candidate_evidence import CandidateEvidence
from backend.app.services.embedding_service import generate_embedding


def build_evidence_embedding_text(
    evidence: CandidateEvidence,
) -> str:
    """
    Build the text representation that will be embedded.
    """

    return (
        f"Category: {evidence.category}\n"
        f"Title: {evidence.title}\n"
        f"Content: {evidence.content}\n"
        f"Source: {evidence.source}"
    )


def embed_candidate_evidence(
    db: Session,
    candidate_id: UUID,
) -> int:
    """
    Generate and store embeddings for all candidate evidence
    that does not already have an embedding.

    Returns the number of records embedded.
    """

    evidence_records = (
        db.query(CandidateEvidence)
        .filter(
            CandidateEvidence.candidate_id == candidate_id,
            CandidateEvidence.embedding.is_(None),
        )
        .all()
    )

    embedded_count = 0

    for evidence in evidence_records:
        text = build_evidence_embedding_text(evidence)

        embedding = generate_embedding(text)

        evidence.embedding = embedding

        embedded_count += 1

    db.commit()

    return embedded_count
