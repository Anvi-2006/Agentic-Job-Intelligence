from uuid import UUID

from pydantic import BaseModel, ConfigDict


class JobCreate(BaseModel):
    external_id: str | None = None
    title: str
    company: str
    location: str | None = None
    description: str
    source: str
    job_url: str | None = None


class JobResponse(BaseModel):
    id: UUID
    external_id: str | None
    title: str
    company: str
    location: str | None
    description: str
    source: str
    job_url: str | None

    model_config = ConfigDict(from_attributes=True)


class JobSearchRequest(BaseModel):
    candidate_id: UUID
    query: str


class JobSearchResult(BaseModel):
    job_id: UUID
    title: str
    company: str
    location: str | None
    description: str
    source: str
    job_url: str | None
    fit_score: float
    recommendation: str
    recommendation_reason: str
    matched_requirements: int
    total_requirements: int
    missing_requirements: list[str]
    partial_requirements: list[str]
    verification_status: str
    verification_confidence: float
    verification_reason: str


class JobSearchResponse(BaseModel):
    candidate_id: UUID
    query: str
    jobs: list[JobSearchResult]
