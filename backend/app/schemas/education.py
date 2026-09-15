from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EducationCreate(BaseModel):
    candidate_id: UUID
    institution: str
    degree: str
    field_of_study: str | None = None
    start_year: int | None = None
    end_year: int | None = None


class EducationResponse(BaseModel):
    id: UUID
    candidate_id: UUID
    institution: str
    degree: str
    field_of_study: str | None
    start_year: int | None
    end_year: int | None

    model_config = ConfigDict(from_attributes=True)