from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ProjectCreate(BaseModel):
    candidate_id: UUID
    name: str
    description: str | None = None
    technologies: str | None = None
    github_url: str | None = None


class ProjectResponse(BaseModel):
    id: UUID
    candidate_id: UUID
    name: str
    description: str | None
    technologies: str | None
    github_url: str | None

    model_config = ConfigDict(from_attributes=True)