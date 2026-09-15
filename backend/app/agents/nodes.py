from backend.app.agents.state import AgentState
from backend.app.core.database import SessionLocal
from backend.app.tools.job_search import search_jobs
from backend.app.services.gemini_service import generate_search_intent
from backend.app.services.job_understanding_service import (
    extract_job_requirements,
    save_job_requirements,
)
from backend.app.services.application_decision_service import (
    decide_application,
)

from backend.app.services.job_matching_service import match_job_requirements
from backend.app.services.job_fit_service import calculate_job_fit_score
from backend.app.services.job_ranking_service import rank_jobs_for_candidate
from backend.app.services.application_package_service import (
    generate_application_package,
)
from backend.app.services.application_package_persistence_service import (
    save_application_package,
)

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
            "preferred_locations": (
                intent.get("locations", [])
                + (
                    ["remote"]
                    if "remote" in user_goal.lower()
                    and "remote" not in [
                        location.lower()
                        for location in intent.get("locations", [])
                    ]
                    else []
                )
            ),
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
    Search jobs using the structured search intent.
    """

    search_keywords = state.get("search_keywords", [])
    preferred_roles = state.get("preferred_roles", [])
    preferred_locations = list(
        state.get("preferred_locations", [])
    )

    user_goal = state.get("user_goal", "").lower()

    if "remote" in user_goal and "remote" not in [
        location.lower()
        for location in preferred_locations
    ]:
        preferred_locations.append("remote")

    if not search_keywords and not preferred_roles:
        return {
            **state,
            "error": "No search intent available for job search.",
        }

    # Prefer the structured role when available.
    # Otherwise fall back to the extracted keywords.
    search_terms = [
        *preferred_roles,
        *state.get("search_keywords", []),
    ]

    # Remove duplicates while preserving order
    search_terms = list(dict.fromkeys(search_terms))

    search_query = " ".join(search_terms)

    db = SessionLocal()

    try:
        jobs = search_jobs(
            db=db,
            keywords=search_query,
        )

        # If locations were identified, keep jobs whose location
        # matches the user's preferred location.
        if preferred_locations:
            filtered_jobs = []

            for job in jobs:
                job_location = (job.get("location") or "").lower()

                if any(
                    location in job_location
                    for location in preferred_locations
                ):
                    filtered_jobs.append(job)

            jobs = filtered_jobs

        return {
            **state,
            "job_ids": [
                job["job_id"]
                for job in jobs
            ],
            "tool_result": {
                "tool": "search_jobs",
                "jobs": jobs,
                "count": len(jobs),
                "search_query": search_query,
                "preferred_locations": preferred_locations,
            },
            "messages": [
                *state.get("messages", []),
                f"Job search completed. Found {len(jobs)} jobs.",
            ],
            "decision": "JOBS_FOUND",
        }

    finally:
        db.close()
        
def understand_jobs_node(state: AgentState) -> AgentState:
    """
    Understand the jobs returned by the job search tool
    by extracting and storing their requirements.
    """

    jobs = state.get("tool_result", {}).get("jobs", [])

    if not jobs:
        return {
            **state,
            "error": "No jobs available for job understanding.",
            "decision": "NO_JOBS_TO_UNDERSTAND",
            "messages": [
                *state.get("messages", []),
                "No jobs available for job understanding.",
            ],
        }

    db = SessionLocal()

    try:
        understood_jobs = []

        for job in jobs:
            requirements = extract_job_requirements(
                job.get("description", "")
            )

            saved_requirements = save_job_requirements(
                db=db,
                job_id=job["job_id"],
                requirements=requirements,
            )

            understood_jobs.append(
                {
                    "job_id": job["job_id"],
                    "title": job["title"],
                    "company": job["company"],
                    "requirements": [
                        requirement.requirement
                        for requirement in saved_requirements
                    ],
                }
            )

        return {
            **state,
            "tool_result": {
                **state.get("tool_result", {}),
                "understood_jobs": understood_jobs,
            },
            "messages": [
                *state.get("messages", []),
                f"Understood {len(understood_jobs)} jobs.",
            ],
            "decision": "JOBS_UNDERSTOOD",
        }

    finally:
        db.close()
        
def match_and_score_jobs_node(state: AgentState) -> AgentState:
    """
    Match the candidate's evidence against each discovered job
    and calculate an overall fit score.
    """

    candidate_id = state.get("candidate_id")
    jobs = state.get("tool_result", {}).get("jobs", [])

    if not candidate_id:
        return {
            **state,
            "error": "No candidate ID available for job matching.",
            "decision": "MATCHING_FAILED",
            "messages": [
                *state.get("messages", []),
                "Job matching failed because candidate ID is missing.",
            ],
        }

    if not jobs:
        return {
            **state,
            "error": "No jobs available for matching.",
            "decision": "NO_JOBS_TO_MATCH",
            "messages": [
                *state.get("messages", []),
                "No jobs available for matching.",
            ],
        }

    db = SessionLocal()

    try:
        match_results = []
        fit_results = []

        for job in jobs:
            job_id = job["job_id"]

            matches = match_job_requirements(
                db=db,
                candidate_id=candidate_id,
                job_id=job_id,
            )

            fit = calculate_job_fit_score(
                db=db,
                candidate_id=candidate_id,
                job_id=job_id,
            )

            match_results.append(
                {
                    "job_id": job_id,
                    "matches": matches,
                }
            )

            fit_results.append(
                {
                    "job_id": job_id,
                    "title": job["title"],
                    "company": job["company"],
                    "location": job.get("location"),
                    **fit,
                }
            )

        return {
            **state,
            "match_results": match_results,
            "fit_results": fit_results,
            "messages": [
                *state.get("messages", []),
                f"Matched candidate against {len(jobs)} jobs.",
                f"Calculated fit scores for {len(jobs)} jobs.",
            ],
            "decision": "JOBS_MATCHED",
        }

    finally:
        db.close()
        
        
def rank_jobs_node(state: AgentState) -> AgentState:
    candidate_id = state.get("candidate_id")

    if not candidate_id:
        return {
            **state,
            "error": "No candidate ID available for job ranking.",
            "decision": "RANKING_FAILED",
            "messages": [
                *state.get("messages", []),
                "Job ranking failed because candidate ID is missing.",
            ],
        }

    job_ids = [
        job["job_id"]
        for job in state.get("tool_result", {}).get("jobs", [])
    ]

    if not job_ids:
        return {
            **state,
            "error": "No discovered jobs available for ranking.",
            "decision": "NO_JOBS_TO_RANK",
            "messages": [
                *state.get("messages", []),
                "No discovered jobs available for ranking.",
            ],
        }

    db = SessionLocal()

    try:
        ranked_jobs = rank_jobs_for_candidate(
            db=db,
            candidate_id=candidate_id,
            job_ids=job_ids,
        )

        return {
            **state,
            "ranked_jobs": ranked_jobs,
            "messages": [
                *state.get("messages", []),
                f"Ranked {len(ranked_jobs)} discovered jobs for the candidate.",
            ],
            "decision": "JOBS_RANKED",
        }

    finally:
        db.close()
        
def decide_applications_node(state: AgentState) -> AgentState:
    ranked_jobs = state.get("ranked_jobs", [])

    if not ranked_jobs:
        return {
            **state,
            "error": "No ranked jobs available for application decisions.",
            "decision": "NO_JOBS_TO_DECIDE",
            "messages": [
                *state.get("messages", []),
                "No ranked jobs available for application decisions.",
            ],
        }

    application_decisions = []

    for job in ranked_jobs:
        application_decision = decide_application(
            fit_score=job["fit_score"],
            missing_requirements=job["missing_requirements"],
            partial_requirements=job["partial_requirements"],
        )

        application_decisions.append(
            {
                "job_id": job["job_id"],
                "title": job["title"],
                "company": job["company"],
                "fit_score": job["fit_score"],
                "decision": application_decision["decision"],
                "reason": application_decision["reason"],
                "missing_requirements": application_decision[
                    "missing_requirements"
                ],
                "partial_requirements": application_decision[
                    "partial_requirements"
                ],
            }
        )

    return {
        **state,
        "application_decisions": application_decisions,
        "messages": [
            *state.get("messages", []),
            f"Generated application decisions for {len(application_decisions)} jobs.",
        ],
        "decision": "APPLICATIONS_DECIDED",
    }
    

def prepare_application_packages_node(state: AgentState) -> AgentState:
    """
    Generate evidence-grounded application packages for jobs
    that the agent recommends applying to or reviewing.
    """

    candidate_id = state.get("candidate_id")
    application_decisions = state.get("application_decisions", [])

    if not candidate_id:
        return {
            **state,
            "error": "No candidate ID available for application preparation.",
            "decision": "APPLICATION_PREPARATION_FAILED",
            "messages": [
                *state.get("messages", []),
                "Application preparation failed because candidate ID is missing.",
            ],
        }

    if not application_decisions:
        return {
            **state,
            "error": "No application decisions available for preparation.",
            "decision": "NO_APPLICATIONS_TO_PREPARE",
            "messages": [
                *state.get("messages", []),
                "No application decisions available for application preparation.",
            ],
        }

    application_packages = []

    db = SessionLocal()

    try:
        for application in application_decisions:
            decision = application["decision"]

            # Only prepare packages for jobs worth applying to
            # or reviewing.
            if decision not in {"apply", "review"}:
                continue

            package = generate_application_package(
                db=db,
                candidate_id=candidate_id,
                job_id=application["job_id"],
            )

            save_application_package(
                db=db,
                candidate_id=candidate_id,
                job_id=application["job_id"],
                package=package,
                agent_decision=decision,
            )

            application_packages.append(package)
            
            
        return {
            **state,
            "application_packages": application_packages,
            "messages": [
                *state.get("messages", []),
                (
                    f"Prepared application packages for "
                    f"{len(application_packages)} jobs."
                ),
            ],
            "decision": "APPLICATION_PACKAGES_READY",
        }

    except Exception as exc:
        return {
            **state,
            "error": f"Application preparation failed: {str(exc)}",
            "messages": [
                *state.get("messages", []),
                "Application package generation failed.",
            ],
            "decision": "APPLICATION_PREPARATION_FAILED",
        }

    finally:
        db.close()