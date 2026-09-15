from uuid import UUID

from pydantic import BaseModel


class ApplicationReadinessResponse(BaseModel):
    candidate_id: UUID
    job_id: UUID

    fit_score: float

    readiness_score: float
    readiness_level: str

    matched_requirements: int
    partial_requirements: list[str]
    missing_requirements: list[str]

    evidence_count: int

    recommendation: str
    reasons: list[str]