import re

from sqlalchemy.orm import Session

from backend.app.models.job_requirement import JobRequirement


KNOWN_REQUIREMENTS = [
    "Python",
    "Java",
    "C++",
    "JavaScript",
    "TypeScript",
    "React",
    "FastAPI",
    "Django",
    "Node.js",
    "SQL",
    "PostgreSQL",
    "MongoDB",
    "REST APIs",
    "Databases",
    "Git",
    "Docker",
    "AWS",
    "Azure",
    "Machine Learning",
    "Deep Learning",
    "Problem Solving",
]


def extract_job_requirements(description: str) -> list[str]:
    """
    Extract known technical and professional requirements
    from a job description.
    """

    found_requirements = []

    for requirement in KNOWN_REQUIREMENTS:
        pattern = re.escape(requirement)

        if re.search(
            rf"\b{pattern}\b",
            description,
            re.IGNORECASE,
        ):
            found_requirements.append(requirement)

    return found_requirements


def save_job_requirements(
    db: Session,
    job_id,
    requirements: list[str],
) -> list[JobRequirement]:
    """
    Save extracted requirements for a job without creating duplicates.
    """

    existing_requirements = (
        db.query(JobRequirement)
        .filter(JobRequirement.job_id == job_id)
        .all()
    )

    existing_names = {
        requirement.requirement.lower()
        for requirement in existing_requirements
    }

    saved_requirements = list(existing_requirements)

    for requirement in requirements:
        if requirement.lower() in existing_names:
            continue

        job_requirement = JobRequirement(
            job_id=job_id,
            requirement=requirement,
            requirement_type="skill",
            importance="required",
        )

        db.add(job_requirement)
        saved_requirements.append(job_requirement)
        existing_names.add(requirement.lower())

    db.commit()

    for job_requirement in saved_requirements:
        db.refresh(job_requirement)

    return saved_requirements