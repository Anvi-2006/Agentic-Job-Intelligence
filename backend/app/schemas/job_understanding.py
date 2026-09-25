from uuid import UUID

from pydantic import BaseModel, Field


class JobRequirementUnderstanding(BaseModel):
    requirement: str
    normalized_name: str
    original_text: str | None = None
    context: str | None = None
    requirement_type: str
    category: str
    importance: str
    confidence: float = Field(ge=0.0, le=1.0)
    source: str


class JobUnderstandingResponse(BaseModel):
    job_id: UUID
    requirements: list[JobRequirementUnderstanding]
    total_requirements: int