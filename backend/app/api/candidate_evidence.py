from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.candidate_evidence import (
    CandidateEvidenceCreate,
    CandidateEvidenceResponse,
)
from backend.app.services.candidate_evidence_service import (
    create_candidate_evidence,
    get_candidate_evidence,
    get_candidate_evidence_list,
)


router = APIRouter(
    prefix="/api/candidate-evidence",
    tags=["Candidate Evidence"],
)


@router.post(
    "",
    response_model=CandidateEvidenceResponse,
    status_code=201,
)
def create_candidate_evidence_endpoint(
    evidence_data: CandidateEvidenceCreate,
    db: Session = Depends(get_db),
):
    return create_candidate_evidence(db, evidence_data)


@router.get(
    "/candidate/{candidate_id}",
    response_model=list[CandidateEvidenceResponse],
)
def get_candidate_evidence_list_endpoint(
    candidate_id: UUID,
    db: Session = Depends(get_db),
):
    return get_candidate_evidence_list(db, candidate_id)


@router.get(
    "/{evidence_id}",
    response_model=CandidateEvidenceResponse,
)
def get_candidate_evidence_endpoint(
    evidence_id: UUID,
    db: Session = Depends(get_db),
):
    evidence = get_candidate_evidence(db, evidence_id)

    if evidence is None:
        raise HTTPException(
            status_code=404,
            detail="Candidate evidence not found",
        )

    return evidence
