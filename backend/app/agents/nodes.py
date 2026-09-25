from backend.app.agents.state import AgentState
from backend.app.core.database import SessionLocal
from backend.app.tools.job_search import search_jobs
from backend.app.services.gemini_service import generate_search_intent
from backend.app.tools.external_job_search import search_external_jobs
from backend.app.services.job_service import upsert_external_job
from backend.app.core.config import settings
from backend.app.services.job_discovery_service import rank_discovery_jobs
from backend.app.services.job_verification_service import verify_job


def initialize_agent(state: AgentState) -> AgentState:
    """
    Initialize the job intelligence agent.

    The agent receives the user's goal and prepares
    the initial state for the workflow.
    """
    user_goal = state.get("user_goal", "").strip()

    if not user_goal:
        return {
            **state,
            "error": "No user goal provided.",
        }

    return {
        **state,
        "messages": [
            "Agent initialized.",
            f"User goal received: {user_goal}",
        ],
        "decision": "START",
    }

def understand_search_intent(state: AgentState) -> AgentState:
    """
    Use Gemini to convert the user's natural-language goal
    into structured job-search intent.
    """

    user_goal = state.get("user_goal", "").strip()

    if not user_goal:
        return {
            **state,
            "error": "No user goal available for intent understanding.",
        }

    try:
        intent = generate_search_intent(user_goal)

        return {
            **state,
            "search_keywords": [
                *intent.get("roles", []),
                *intent.get("skills", []),
            ],
            "preferred_roles": intent.get("roles", []),
            "preferred_skills": intent.get("skills", []),
            "preferred_locations": intent.get("locations", []),
            "work_mode": intent.get("work_mode"),
            "messages": [
                *state.get("messages", []),
                "Search intent understood using Gemini.",
            ],
            "tool_result": {
                **state.get("tool_result", {}),
                "search_intent": intent,
            },
            "decision": "INTENT_UNDERSTOOD",
        }

    except Exception as exc:
        return {
            **state,
            "error": f"Intent understanding failed: {str(exc)}",
            "messages": [
                *state.get("messages", []),
                "Gemini intent understanding failed.",
            ],
            "decision": "INTENT_FAILED",
        }

def search_jobs_node(state: AgentState) -> AgentState:
    """
    Discover jobs using the structured search intent.

    Discovery intentionally remains lightweight. Candidate-fit
    intelligence is calculated later when the user opens a job.
    """

    search_keywords = state.get("search_keywords", [])
    preferred_roles = state.get("preferred_roles", [])
    preferred_locations = list(
        state.get("preferred_locations", [])
    )

    work_mode = state.get("work_mode")

    if not search_keywords and not preferred_roles:
        return {
            **state,
            "error": "No search intent available for job search.",
        }

    search_terms = [
        *preferred_roles,
        *search_keywords,
    ]

    search_terms = list(dict.fromkeys(search_terms))
    search_query = " ".join(search_terms)

    db = SessionLocal()

    try:
        jobs = search_jobs(
            db=db,
            keywords=search_query,
        )

        external_jobs = search_external_jobs(
            greenhouse_boards=[
                item.strip()
                for item in settings.greenhouse_boards.split(",")
                if item.strip()
            ],
            lever_companies=[
                item.strip()
                for item in settings.lever_companies.split(",")
                if item.strip()
            ],
            roles=preferred_roles,
            skills=search_keywords,
            locations=preferred_locations,
        )

        existing_job_ids = {
            job["job_id"]
            for job in jobs
        }

        for external_job in external_jobs:
            job = upsert_external_job(
                db,
                external_job,
            )

            job_id = str(job.id)

            normalized_external_job = {
                "job_id": job_id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "description": job.description,
                "source": job.source,
                "job_url": job.job_url,
            }

            existing_index = next(
                (
                    index
                    for index, existing_job in enumerate(jobs)
                    if existing_job["job_id"] == job_id
                ),
                None,
            )

            if existing_index is not None:
                jobs[existing_index] = normalized_external_job
            else:
                jobs.append(normalized_external_job)
                existing_job_ids.add(job_id)

        # Rank jobs using lightweight discovery relevance first.
        #
        # IMPORTANT:
        # Candidate-fit intelligence and external verification are
        # intentionally excluded from this first pass. This keeps
        # discovery cheap even when hundreds of jobs are available.
        ranked_jobs = rank_discovery_jobs(
        jobs,
        roles=preferred_roles,
        skills=state.get("preferred_skills", []),
        locations=preferred_locations,
        work_mode=work_mode,
        limit=25,
    )

        # Verify only the jobs that survived discovery ranking.
        #
        # Verification is a network operation, so we deliberately
        # avoid performing it for jobs that will never be displayed.
        verified_jobs = []

        for job in ranked_jobs:
            verification = verify_job(job)

            verified_jobs.append(
                {
                    **job,
                    **verification,
                }
            )

        lightweight_jobs = []

        for job in verified_jobs:

            description = job.get("description") or ""

            lightweight_jobs.append(
                {
                    "job_id": job["job_id"],
                    "title": job["title"],
                    "company": job["company"],
                    "location": job.get("location"),
                    "description_preview": (
                        f"{description[:240]}"
                        f"{'...' if len(description) > 240 else ''}"
                    ),
                    "source": job["source"],
                    "job_url": job.get("job_url"),
                    "verification_status": job[
                        "verification_status"
                    ],
                    "verification_confidence": job[
                        "verification_confidence"
                    ],
                    "verification_reason": job[
                        "verification_reason"
                    ],
                    "discovery_score": job[
                        "discovery_score"
                    ],
                }
            )

        return {
            **state,
            "job_ids": [
                job["job_id"]
                for job in lightweight_jobs
            ],
            "tool_result": {
                "tool": "search_jobs",
                "jobs": lightweight_jobs,
                "count": len(lightweight_jobs),
                "search_query": search_query,
                "preferred_locations": preferred_locations,
            },
            "messages": [
                *state.get("messages", []),
                (
                    "Job discovery completed. "
                    f"Surfaced {len(lightweight_jobs)} relevant jobs."
                ),
            ],
            "decision": "JOBS_FOUND",
        }

    finally:
        db.close()
