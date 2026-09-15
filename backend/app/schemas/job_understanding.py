from uuid import UUID

from pydantic import BaseModel


class JobUnderstandingResponse(BaseModel):
    job_id: UUID
    requirements: list[str]
    total_requirements: int