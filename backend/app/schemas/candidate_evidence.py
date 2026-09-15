from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CandidateEvidenceCreate(BaseModel):
    candidate_id: UUID
    category: str
    title: str
    content: str
    source: str


class CandidateEvidenceResponse(BaseModel):
    id: UUID
    candidate_id: UUID
    category: str
    title: str
    content: str
    source: str

    model_config = ConfigDict(from_attributes=True)