from uuid import UUID

from pydantic import BaseModel, Field


class JobIntelligenceJobResponse(BaseModel):
    id: UUID
    title: str
    company: str
    location: str | None
    description: str
    source: str
    job_url: str | None


class JobVerificationResponse(BaseModel):
    verification_status: str
    verification_confidence: float
    verification_reason: str


class JobRequirementIntelligenceResponse(BaseModel):
    id: UUID
    requirement: str
    normalized_name: str
    original_text: str
    context: str
    requirement_type: str
    category: str
    importance: str

    match_status: str
    matched: bool
    confidence: float
    reason: str
    evidence_match_type: str | None
    evidence_ids: list[UUID] = Field(default_factory=list)


class JobIntelligenceResponse(BaseModel):
    candidate_id: UUID
    job_id: UUID

    job: JobIntelligenceJobResponse
    verification: JobVerificationResponse

    requirements: list[JobRequirementIntelligenceResponse]

    fit: dict
    skill_gaps: list[dict]