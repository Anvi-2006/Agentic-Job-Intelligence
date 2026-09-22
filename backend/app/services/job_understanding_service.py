import re
from sqlalchemy.orm import Session
from backend.app.models.job_requirement import JobRequirement

KNOWN_REQUIREMENTS = [
    # Programming
    "Python",
    "Java",
    "C++",
    "JavaScript",
    "TypeScript",

    # Frameworks
    "React",
    "FastAPI",
    "Django",
    "Node.js",

    # Data / backend
    "SQL",
    "PostgreSQL",
    "MongoDB",
    "REST APIs",
    "Databases",

    # Engineering tools
    "Git",
    "Docker",
    "AWS",
    "Azure",

    # AI / ML
    "Machine Learning",
    "Deep Learning",
    "Natural Language Processing",
    "Computer Vision",
    "Large Language Models",
    "LLMs",
    "Generative AI",

    # Core engineering
    "Algorithms",
    "Data Structures",
    "Problem Solving",
    "System Design",

    # Professional
    "Communication",
    "Teamwork",
    "Leadership",

    # Software engineering
    "Software Engineering",
    "Backend Development",
    "API Development",
    "Distributed Systems",
    "Scalable Systems",

    # AI / LLM engineering
    "AI Engineering",
    "LLM Applications",
    "AI Systems",
    "Prompt Engineering",
    "Model Evaluation",
    "AI Agents",
    "Agentic AI",

    # Infrastructure / deployment
    "Kubernetes",
    "CI/CD",
    "Linux",
    "Cloud Computing",

    # Collaboration
    "Cross-functional Collaboration",
    "Technical Writing",
]

REQUIREMENT_ALIASES = {
    "Large Language Models": [
        "large language models",
        "llms",
        "llm",
        "llm applications",
        "llm systems",
    ],
    "Machine Learning": [
        "machine learning",
        "ml",
        "machine-learning",
    ],
    "Generative AI": [
        "generative ai",
        "genai",
    ],
    "REST APIs": [
        "rest api",
        "rest apis",
        "restful api",
        "restful apis",
    ],
}


def extract_job_requirements(description: str) -> list[str]:
    found_requirements = []

    for requirement in KNOWN_REQUIREMENTS:
        if re.search(
            rf"\b{re.escape(requirement)}\b",
            description,
            re.IGNORECASE,
        ):
            found_requirements.append(requirement)

    for requirement, aliases in REQUIREMENT_ALIASES.items():
        if any(
            re.search(rf"\b{re.escape(alias)}\b", description, re.IGNORECASE)
            for alias in aliases
        ):
            if requirement not in found_requirements:
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
