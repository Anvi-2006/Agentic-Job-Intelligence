import re
from urllib.parse import urljoin

import requests


def search_greenhouse_jobs(
    board_token: str,
    timeout: int = 10,
) -> list[dict]:
    """Fetch published jobs from a Greenhouse job board."""

    url = (
        f"https://boards-api.greenhouse.io/v1/boards/"
        f"{board_token}/jobs"
    )

    response = requests.get(
        url,
        params={"content": "true"},
        timeout=timeout,
    )
    response.raise_for_status()

    data = response.json()

    jobs = []

    for job in data.get("jobs", []):
        location = job.get("location") or {}

        jobs.append(
            {
                "external_id": str(job.get("id")),
                "title": job.get("title", ""),
                "company": board_token,
                "location": location.get("name"),
                "description": job.get("content", ""),
                "source": "greenhouse",
                "job_url": job.get("absolute_url"),
            }
        )

    return jobs


def search_lever_jobs(
    company_slug: str,
    timeout: int = 10,
) -> list[dict]:
    """Fetch published jobs from a Lever company posting page."""

    url = f"https://api.lever.co/v0/postings/{company_slug}"

    response = requests.get(
        url,
        params={"mode": "json"},
        timeout=timeout,
    )
    response.raise_for_status()

    jobs = []

    for job in response.json():
        categories = job.get("categories") or {}

        jobs.append(
            {
                "external_id": str(job.get("id")),
                "title": job.get("text", ""),
                "company": company_slug,
                "location": categories.get("location"),
                "description": job.get("descriptionPlain", ""),
                "source": "lever",
                "job_url": job.get("hostedUrl"),
            }
        )

    return jobs


def matches_text(text: str, term: str) -> bool:
    return bool(
        re.search(
            rf"\b{re.escape(term.lower().strip())}\b",
            text,
        )
    )

def search_external_jobs(
    greenhouse_boards: list[str] | None = None,
    lever_companies: list[str] | None = None,
    roles: list[str] | None = None,
    skills: list[str] | None = None,
    locations: list[str] | None = None,
) -> list[dict]:
    """Search configured external job sources."""

    jobs = []

    for board in greenhouse_boards or []:
        try:
            jobs.extend(search_greenhouse_jobs(board))
        except requests.RequestException:
            continue

    for company in lever_companies or []:
        try:
            jobs.extend(search_lever_jobs(company))
        except requests.RequestException:
            continue

    terms = [
        *(roles or []),
        *(skills or []),
    ]

    if terms:
        def matches(job: dict) -> bool:
            title = job.get("title") or ""
            description = job.get("description") or ""

            role_match = any(
                matches_text(title, term)
                for term in roles or []
            )

            skill_matches = sum(
                matches_text(
                    f"{title} {description}",
                    term,
                )
                for term in skills or []
            )

            return role_match or skill_matches >= 2

        jobs = [job for job in jobs if matches(job)]

    if locations:
        location_terms = [
            item.lower().strip()
            for item in locations
            if item.strip()
        ]

        jobs = [
            job
            for job in jobs
            if any(
                term in (job.get("location") or "").lower()
                for term in location_terms
            )
        ]

    return jobs