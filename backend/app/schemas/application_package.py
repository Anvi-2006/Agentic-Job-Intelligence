from uuid import UUID

from pydantic import BaseModel


class ApplicationAnswer(BaseModel):
    question: str
    answer: str
    evidence_used: list[str]


class ApplicationPackageResponse(BaseModel):
    application_id:UUID
    candidate_id: UUID
    job_id: UUID

    company: str
    job_title: str

    readiness_score: float
    recommendation: str

    tailored_summary: str
    cover_letter: str

    key_strengths: list[str]
    missing_requirements: list[str]

    application_questions: list[ApplicationAnswer]

    evidence_used: list[str]

    unsupported_claims: list[str]
    is_valid: bool