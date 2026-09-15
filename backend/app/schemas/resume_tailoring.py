from uuid import UUID

from pydantic import BaseModel


class EvidenceUsage(BaseModel):
    evidence_id: UUID
    title: str
    matched_requirement: str
    match_type: str
    relevance_score: float


class TailoredResumeResponse(BaseModel):
    candidate_id: UUID
    job_id: UUID
    summary: str
    fit_score: float
    missing_requirements: list[str]
    partial_requirements: list[str]
    evidence_used: list[EvidenceUsage]
    unsupported_claims: list[str]
    is_valid: bool