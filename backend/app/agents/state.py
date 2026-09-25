from typing import TypedDict


class AgentState(TypedDict, total=False):
    candidate_id: str

    # User's original request
    user_goal: str

    # Structured search intent
    search_keywords: list[str]
    preferred_roles: list[str]
    preferred_skills: list[str]
    preferred_locations: list[str]
    work_mode: str | None

    # Job search results
    job_ids: list[str]
    current_job_id: str

    match_results: list[dict]
    fit_results: list[dict]
    ranked_jobs: list[dict]
    application_decisions: list[dict]
    application_packages: list[dict]
    
    # Tool and agent information
    tool_result: dict
    decision: str
    messages: list[str]
    error: str | None
    