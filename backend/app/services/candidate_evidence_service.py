from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models.candidate_evidence import CandidateEvidence
from backend.app.schemas.candidate_evidence import CandidateEvidenceCreate


def create_candidate_evidence(
    db: Session,
    evidence_data: CandidateEvidenceCreate,
) -> CandidateEvidence:
    evidence = CandidateEvidence(
        candidate_id=evidence_data.candidate_id,
        category=evidence_data.category,
        title=evidence_data.title,
        content=evidence_data.content,
        source=evidence_data.source,
    )

    db.add(evidence)
    db.commit()
    db.refresh(evidence)

    return evidence


def get_candidate_evidence(
    db: Session,
    evidence_id: UUID,
) -> CandidateEvidence | None:
    return db.get(CandidateEvidence, evidence_id)


def get_candidate_evidence_list(
    db: Session,
    candidate_id: UUID,
) -> list[CandidateEvidence]:
    return (
        db.query(CandidateEvidence)
        .filter(CandidateEvidence.candidate_id == candidate_id)
        .all()
    )


def delete_resume_evidence(
    db: Session,
    candidate_id: UUID,
) -> int:
    """
    Delete only evidence that was generated from a resume.

    Evidence from other sources such as GitHub, manual input,
    or candidate skills is preserved.
    """

    deleted_count = (
        db.query(CandidateEvidence)
        .filter(
            CandidateEvidence.candidate_id == candidate_id,
            CandidateEvidence.source == "resume",
        )
        .delete(
            synchronize_session=False,
        )
    )

    db.commit()

    return deleted_count