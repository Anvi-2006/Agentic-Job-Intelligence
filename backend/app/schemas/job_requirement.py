from uuid import UUID

from pydantic import BaseModel, ConfigDict


class JobRequirementCreate(BaseModel):
    job_id: UUID
    requirement: str
    requirement_type: str
    importance: str


class JobRequirementResponse(BaseModel):
    id: UUID
    job_id: UUID
    requirement: str
    requirement_type: str
    importance: str

    model_config = ConfigDict(from_attributes=True)