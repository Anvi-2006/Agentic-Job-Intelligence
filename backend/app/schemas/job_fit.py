from uuid import UUID

from pydantic import BaseModel

from backend.app.schemas.job_matching import RequirementMatchResponse

class JobFitResponse(BaseModel):
    candidate_id: UUID
    job_id: UUID
    score: float
    matched_requirements: int
    total_requirements: int
    missing_requirements: list[str]
    partial_requirements: list[str]
    matches: list[RequirementMatchResponse]