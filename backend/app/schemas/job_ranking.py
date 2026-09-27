from uuid import UUID

from pydantic import BaseModel, Field


class JobRankingRequest(BaseModel):
    job_ids: list[UUID] = Field(min_length=1)


class RankedJobResponse(BaseModel):
    job_id: UUID
    title: str
    company: str
    location: str | None
    job_url: str | None
    fit_score: float
    recommendation: str
    recommendation_reason: str
    matched_requirements: int
    total_requirements: int
    missing_requirements: list[str]
    partial_requirements: list[str]


class JobRankingResponse(BaseModel):
    candidate_id: UUID
    jobs: list[RankedJobResponse]
