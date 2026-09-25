import re
from html import unescape

import requests

def clean_job_description(html: str) -> str:
    text = html or ""

    # Greenhouse may return HTML that is itself HTML-escaped.
    # Decode entities first so encoded tags become real HTML.
    text = unescape(text)

    # Remove the now-decoded HTML tags.
    text = re.sub(r"<[^>]+>", " ", text)

    # Decode any remaining entities in the text.
    text = unescape(text)

    # Normalize whitespace.
    text = re.sub(r"\s+", " ", text).strip()

    # Repair common UTF-8 -> Windows-1252 mojibake if encountered.
    if "Ã¢" in text or "Ãƒ" in text:
        try:
            text = text.encode("latin1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass

    return text


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
                "description": clean_job_description(job.get("content", "")),
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
                "description": clean_job_description(job.get("descriptionPlain", "")),
                "source": "lever",
                "job_url": job.get("hostedUrl"),
            }
        )

    return jobs


def matches_text(text: str, term: str) -> bool:
    text = text.lower()
    term = term.lower().strip()

    if not term:
        return False

    if re.search(rf"\b{re.escape(term)}\b", text):
        return True

    tokens = term.split()

    if len(tokens) == 1:
        return re.search(rf"\b{re.escape(tokens[0])}\b", text) is not None

    return all(
        re.search(rf"\b{re.escape(token)}\b", text)
        for token in tokens
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

    def normalize_identity(value: str | None) -> str:
        return re.sub(
            r"[^a-z0-9]+",
            " ",
            (value or "").lower(),
        ).strip()


    def job_identity(job: dict) -> tuple[str, str, str]:
        """
        Build a stable identity for discovery-level deduplication.

        Prefer the source + external ID when available.
        Fall back to normalized company + title + location
        when external IDs are missing or inconsistent.
        """

        source = normalize_identity(job.get("source"))
        external_id = normalize_identity(job.get("external_id"))

        if source and external_id:
            return ("source", source, external_id)

        company = normalize_identity(job.get("company"))
        title = normalize_identity(job.get("title"))
        location = normalize_identity(job.get("location"))

        return (
            "content",
            company,
            f"{title}|{location}",
        )


    seen = set()
    unique_jobs = []

    for job in jobs:
        identity = job_identity(job)

        if identity in seen:
            continue

        seen.add(identity)
        unique_jobs.append(job)

    return unique_jobs
