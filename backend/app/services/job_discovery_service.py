from collections.abc import Iterable


def _normalize(value: str | None) -> str:
    return " ".join((value or "").lower().split())


def _contains_term(text: str, term: str) -> bool:
    normalized_text = _normalize(text)
    normalized_term = _normalize(term)

    if not normalized_term:
        return False

    return normalized_term in normalized_text


def calculate_discovery_score(
    job: dict,
    *,
    roles: Iterable[str] = (),
    skills: Iterable[str] = (),
    locations: Iterable[str] = (),
    work_mode: str | None = None,
) -> float:
    """
    Calculate a lightweight search-relevance score.

    This is discovery relevance, not candidate fit.
    It intentionally avoids requirement extraction, embeddings,
    Gemini reasoning, and candidate evidence matching.
    """

    title = _normalize(job.get("title"))
    description = _normalize(job.get("description"))
    company = _normalize(job.get("company"))
    location = _normalize(job.get("location"))

    roles = [
        _normalize(role)
        for role in roles
        if _normalize(role)
    ]

    skills = [
        _normalize(skill)
        for skill in skills
        if _normalize(skill)
    ]

    locations = [
        _normalize(location_term)
        for location_term in locations
        if _normalize(location_term)
    ]

    score = 0.0

    # Role relevance carries the most weight because the job title
    # is the strongest lightweight discovery signal.
    for role in roles:
        if title == role:
            score += 50.0
        elif title.startswith(f"{role},"):
            score += 46.0
        elif title.startswith(f"{role} "):
            score += 46.0
        elif _contains_term(title, role):
            score += 40.0
        elif _contains_term(description, role):
            score += 15.0

    # Work-mode relevance
    if work_mode:
        normalized_work_mode = _normalize(work_mode)

        if normalized_work_mode == "remote":
            remote_indicators = (
                "remote",
                "remote-friendly",
                "work from home",
            )

            location_has_remote_signal = any(
                _contains_term(location, indicator)
                for indicator in remote_indicators
            )

            description_has_remote_signal = any(
                _contains_term(description, indicator)
                for indicator in remote_indicators
            )

            if location_has_remote_signal:
                score += 20.0
            elif description_has_remote_signal:
                score += 8.0

        elif normalized_work_mode == "hybrid":
            hybrid_indicators = (
                "hybrid",
                "flexible work",
            )

            if any(
                _contains_term(location, indicator)
                or _contains_term(description, indicator)
                for indicator in hybrid_indicators
            ):
                score += 20.0

        elif normalized_work_mode == "onsite":
            onsite_indicators = (
                "onsite",
                "on-site",
                "in office",
                "office-based",
            )

            if any(
                _contains_term(location, indicator)
                or _contains_term(description, indicator)
                for indicator in onsite_indicators
            ):
                score += 20.0

        seniority_terms = (
        "staff",
        "senior",
        "principal",
        "director",
        "manager",
        "lead",
        "head",
        "vp",
    )

    seniority_penalty = 0.0

    for term in seniority_terms:
        if title.startswith(term) or f" {term} " in title:
            seniority_penalty = 8.0
            break

    score -= seniority_penalty

    # Skill relevance provides additional search context.
    matched_skills = 0

    for skill in skills:
        if _contains_term(title, skill):
            score += 12.0
            matched_skills += 1
        elif _contains_term(description, skill):
            score += 6.0
            matched_skills += 1

    if matched_skills:
        score += min(matched_skills * 2.0, 10.0)

    # Location relevance.
    for location_term in locations:
        if _contains_term(location, location_term):
            score += 15.0
            break

    # Remote is often represented in either location or description.
    if "remote" in locations:
        if (
            _contains_term(location, "remote")
            or _contains_term(description, "remote")
        ):
            score += 15.0

    # Source verification is a useful trust signal, but should never
    # dominate relevance.
    verification_status = job.get("verification_status")

    if verification_status == "OFFICIAL_SOURCE":
        score += 8.0
    elif verification_status == "VERIFIED_SOURCE":
        score += 6.0
    elif verification_status == "LINK_REACHABLE":
        score += 3.0

    # Keep discovery scoring focused on query relevance.
    # Source verification is handled after the top results
    # have been selected.

    return round(min(score, 100.0), 2)


def deduplicate_jobs(jobs: list[dict]) -> list[dict]:
    """
    Deduplicate jobs by their canonical database job_id.
    Preserve the first occurrence.
    """

    seen: set[str] = set()
    unique_jobs: list[dict] = []

    for job in jobs:
        job_id = str(job.get("job_id") or "").strip()

        if not job_id or job_id in seen:
            continue

        seen.add(job_id)
        unique_jobs.append(job)

    return unique_jobs


def rank_discovery_jobs(
    jobs: list[dict],
    *,
    roles: Iterable[str] = (),
    skills: Iterable[str] = (),
    locations: Iterable[str] = (),
    work_mode: str | None = None,
    limit: int = 25,
) -> list[dict]:
    """
    Rank discovered jobs using lightweight search relevance.

    This function does not calculate candidate fit.
    """

    unique_jobs = deduplicate_jobs(jobs)

    scored_jobs = []

    for job in unique_jobs:
        discovery_score = calculate_discovery_score(
            job,
            roles=roles,
            skills=skills,
            locations=locations,
            work_mode=work_mode,
        )

        scored_jobs.append(
            {
                **job,
                "discovery_score": discovery_score,
            }
        )

    scored_jobs.sort(
        key=lambda job: (
            job["discovery_score"],
            _normalize(job.get("title")),
            _normalize(job.get("company")),
        ),
        reverse=True,
    )

    return scored_jobs[:limit]
