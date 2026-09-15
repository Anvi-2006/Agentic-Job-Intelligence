from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class ResumeCreate(BaseModel):
    candidate_id: UUID
    file_name: str
    file_path: str | None = None
    raw_text: str | None = None


class ResumeResponse(BaseModel):
    id: UUID
    candidate_id: UUID
    file_name: str
    file_path: str | None
    raw_text: str | None

    model_config = ConfigDict(from_attributes=True)
    
    
class PersonalInfo(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin: str | None = None
    github: str | None = None


class ExperienceItem(BaseModel):
    company: str | None = None
    role: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None
    technologies: list[str] = []


class ProjectItem(BaseModel):
    name: str
    description: str | None = None
    technologies: list[str] = Field(default_factory=list)
    url: str | None = None


class EducationItem(BaseModel):
    institution: str | None = None
    degree: str | None = None
    field_of_study: str | None = None
    dates: str | None = None
    grade: str | None = None


class CertificationItem(BaseModel):
    name: str
    issuer: str | None = None
    date: str | None = None


class CandidateResume(BaseModel):
    personal_info: PersonalInfo = PersonalInfo()
    summary: str | None = None

    skills: list[str] = []

    experience: list[ExperienceItem] = []

    projects: list[ProjectItem] = []

    education: list[EducationItem] = []

    certifications: list[CertificationItem] = []

    achievements: list[str] = []