from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CandidateCreate(BaseModel):
    user_id: UUID
    headline: str | None = None
    summary: str | None = None
    preferred_roles: str | None = None
    preferred_locations: str | None = None


class CandidateResponse(BaseModel):
    id: UUID
    user_id: UUID
    headline: str | None
    summary: str | None
    preferred_roles: str | None
    preferred_locations: str | None

    model_config = ConfigDict(from_attributes=True)