from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SkillCreate(BaseModel):
    name: str


class SkillResponse(BaseModel):
    id: UUID
    name: str

    model_config = ConfigDict(from_attributes=True)


class CandidateSkillCreate(BaseModel):
    skill_id: UUID
    proficiency: str | None = None


class CandidateSkillResponse(BaseModel):
    candidate_id: UUID
    skill_id: UUID
    proficiency: str | None

    model_config = ConfigDict(from_attributes=True)
    