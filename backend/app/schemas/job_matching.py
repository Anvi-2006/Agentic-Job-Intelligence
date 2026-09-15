from uuid import UUID

from pydantic import BaseModel


class RequirementMatchResponse(BaseModel):
    requirement: str
    importance: str
    matched: bool
    evidence_ids: list[UUID]
    match_status: str


class JobMatchingResponse(BaseModel):
    candidate_id: UUID
    job_id: UUID
    matches: list[RequirementMatchResponse]