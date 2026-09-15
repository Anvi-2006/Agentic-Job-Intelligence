from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.candidate_evidence import CandidateEvidence
from backend.app.services.embedding_service import (
    generate_embedding,
    generate_embeddings,
)


def search_candidate_evidence(
    db: Session,
    candidate_id: UUID,
    query: str,
    limit: int = 5,
) -> list[dict]:
    """
    Retrieve candidate evidence using pgvector cosine similarity.
    """

    if not query or not query.strip():
        raise ValueError("Search query cannot be empty")

    if limit < 1:
        raise ValueError("Limit must be at least 1")

    query_embedding = generate_embedding(query)

    return _search_with_embedding(
        db=db,
        candidate_id=candidate_id,
        query_embedding=query_embedding,
        limit=limit,
    )


def search_candidate_evidence_batch(
    db: Session,
    candidate_id: UUID,
    queries: list[str],
    limit: int = 5,
) -> dict[str, list[dict]]:
    """
    Retrieve candidate evidence for multiple queries.

    All query embeddings are generated in a single Gemini
    embedding request, followed by one pgvector search per query.
    """

    if not queries:
        raise ValueError("Queries cannot be empty")

    if any(
        not query or not query.strip()
        for query in queries
    ):
        raise ValueError(
            "Queries cannot contain empty values"
        )

    if limit < 1:
        raise ValueError("Limit must be at least 1")

    embeddings = generate_embeddings(queries)

    results = {}

    for query, embedding in zip(
        queries,
        embeddings,
    ):
        results[query] = _search_with_embedding(
            db=db,
            candidate_id=candidate_id,
            query_embedding=embedding,
            limit=limit,
        )

    return results


def _search_with_embedding(
    db: Session,
    candidate_id: UUID,
    query_embedding: list[float],
    limit: int,
) -> list[dict]:
    """
    Execute pgvector similarity search using an
    already-generated embedding.
    """

    distance = CandidateEvidence.embedding.cosine_distance(
        query_embedding
    )

    similarity = (1 - distance).label(
        "similarity"
    )

    statement = (
        select(
            CandidateEvidence,
            similarity,
        )
        .where(
            CandidateEvidence.candidate_id == candidate_id,
            CandidateEvidence.embedding.is_not(None),
        )
        .order_by(distance)
        .limit(limit)
    )

    results = db.execute(statement).all()

    return [
        {
            "evidence_id": evidence.id,
            "category": evidence.category,
            "title": evidence.title,
            "content": evidence.content,
            "source": evidence.source,
            "similarity": float(score),
        }
        for evidence, score in results
    ]
    

