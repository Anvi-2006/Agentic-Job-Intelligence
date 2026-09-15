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