from pydantic import BaseModel, Field


class SearchIntent(BaseModel):
    roles: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    experience_level: str | None = None
    work_mode: str | None = None
    employment_type: str | None = None
    skills: list[str] = Field(default_factory=list)
    company_preferences: list[str] = Field(default_factory=list)