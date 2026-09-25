from uuid import UUID

from pydantic import BaseModel

from backend.app.schemas.job_matching import RequirementMatchResponse


class ScoreBreakdownResponse(BaseModel):
    requirement: str
    importance: str
    match_status: str
    weight: float
    score_contribution: float
    reason: str
    evidence_ids: list[UUID]


class JobFitResponse(BaseModel):
    candidate_id: UUID
    job_id: UUID

    score: float
    recommendation: str

    matched_requirements: int
    total_requirements: int

    missing_requirements: list[str]
    partial_requirements: list[str]
    matched_requirement_names: list[str]

    matched_weight: float
    total_weight: float

    score_breakdown: list[ScoreBreakdownResponse]

    matches: list[RequirementMatchResponse]