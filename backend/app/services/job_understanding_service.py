import json
import re

from sqlalchemy.orm import Session

from backend.app.models.job_requirement import JobRequirement
from backend.app.services.gemini_service import client


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

    # AI engineering
    "AI Engineering",
    "LLM Applications",
    "AI Systems",
    "Prompt Engineering",
    "Model Evaluation",
    "AI Agents",
    "Agentic AI",

    # Infrastructure
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


def normalize_requirement_name(value: str) -> str:
    """
    Produce a stable canonical requirement name.

    This is intentionally deterministic.
    """

    normalized = value.strip().lower()

    normalized = normalized.replace("-", " ")
    normalized = re.sub(r"\s+", " ", normalized)

    alias_lookup = {}

    for canonical, aliases in REQUIREMENT_ALIASES.items():
        alias_lookup[canonical.lower()] = canonical.lower()

        for alias in aliases:
            alias_lookup[alias.lower()] = canonical.lower()

    return alias_lookup.get(normalized, normalized)


def display_requirement_name(value: str) -> str:
    """
    Convert a normalized requirement into a readable display name.
    """

    normalized = normalize_requirement_name(value)

    special_names = {
        "python": "Python",
        "javascript": "JavaScript",
        "typescript": "TypeScript",
        "c++": "C++",
        "node.js": "Node.js",
        "fastapi": "FastAPI",
        "django": "Django",
        "postgresql": "PostgreSQL",
        "mongodb": "MongoDB",
        "rest apis": "REST APIs",
        "api development": "API Development",
        "machine learning": "Machine Learning",
        "deep learning": "Deep Learning",
        "natural language processing": "Natural Language Processing",
        "computer vision": "Computer Vision",
        "large language models": "Large Language Models",
        "generative ai": "Generative AI",
        "ai engineering": "AI Engineering",
        "ai systems": "AI Systems",
        "ai agents": "AI Agents",
        "agentic ai": "Agentic AI",
        "llm applications": "LLM Applications",
        "prompt engineering": "Prompt Engineering",
        "model evaluation": "Model Evaluation",
        "problem solving": "Problem Solving",
        "data structures": "Data Structures",
        "system design": "System Design",
        "ci/cd": "CI/CD",
        "aws": "AWS",
        "azure": "Azure",
        "docker": "Docker",
        "kubernetes": "Kubernetes",
        "linux": "Linux",
        "sql": "SQL",
        "git": "Git",
    }

    return special_names.get(
        normalized,
        value.strip(),
    )


def extract_deterministic_requirements(
    description: str,
) -> list[dict]:
    """
    Extract obvious requirements using deterministic matching.

    This is a fast/high-confidence first pass.
    """

    results = []
    seen = set()

    for requirement in KNOWN_REQUIREMENTS:

        canonical = normalize_requirement_name(requirement)

        if canonical in seen:
            continue

        aliases = REQUIREMENT_ALIASES.get(
            requirement,
            [requirement],
        )

        matched_text = None

        for alias in aliases:
            pattern = rf"\b{re.escape(alias)}\b"

            match = re.search(
                pattern,
                description,
                re.IGNORECASE,
            )

            if match:
                matched_text = match.group(0)
                break

        if matched_text is None:
            continue

        seen.add(canonical)

        results.append(
            {
                "requirement": display_requirement_name(
                    canonical
                ),
                "normalized_name": canonical,
                "original_text": matched_text,
                "context": _extract_context(
                    description,
                    matched_text,
                ),
                "requirement_type": "skill",
                "category": _infer_category(
                    canonical
                ),
                "importance": _infer_importance(
                    description,
                    matched_text,
                ),
                "confidence": 0.96,
                "source": "deterministic",
            }
        )

    return results


def _extract_context(
    description: str,
    matched_text: str,
    window: int = 180,
) -> str:
    """
    Extract a bounded text window around a requirement.
    """

    index = description.lower().find(
        matched_text.lower()
    )

    if index == -1:
        return matched_text

    start = max(0, index - window)
    end = min(
        len(description),
        index + len(matched_text) + window,
    )

    return description[start:end].strip()


def _infer_category(
    normalized_name: str,
) -> str:

    technical = {
        "python",
        "java",
        "c++",
        "javascript",
        "typescript",
        "fastapi",
        "django",
        "react",
        "node.js",
        "sql",
        "postgresql",
        "mongodb",
        "rest apis",
        "git",
        "docker",
        "aws",
        "azure",
        "kubernetes",
        "linux",
        "machine learning",
        "deep learning",
        "generative ai",
        "large language models",
        "natural language processing",
        "computer vision",
        "ai engineering",
        "ai systems",
        "ai agents",
        "agentic ai",
        "llm applications",
    }

    infrastructure = {
        "kubernetes",
        "docker",
        "aws",
        "azure",
        "cloud computing",
        "linux",
        "ci/cd",
    }

    behavioral = {
        "communication",
        "teamwork",
        "leadership",
        "cross-functional collaboration",
        "technical writing",
        "problem solving",
    }

    if normalized_name in infrastructure:
        return "infrastructure"

    if normalized_name in behavioral:
        return "behavioral"

    if normalized_name in technical:
        return "technical"

    return "general"


def _infer_importance(
    description: str,
    matched_text: str,
) -> str:
    """
    Heuristic importance classification.

    Gemini will later refine this.
    """

    context = _extract_context(
        description,
        matched_text,
        window=220,
    ).lower()

    nice_to_have_patterns = [
        "nice to have",
        "nice-to-have",
        "bonus",
        "plus",
        "preferred",
        "preferred qualification",
        "good to have",
    ]

    required_patterns = [
        "required",
        "must have",
        "must-have",
        "minimum",
        "required qualification",
        "qualifications",
    ]

    if any(
        pattern in context
        for pattern in nice_to_have_patterns
    ):
        return "preferred"

    if any(
        pattern in context
        for pattern in required_patterns
    ):
        return "required"

    return "required"


def _clean_llm_json(
    response_text: str,
) -> str:

    response_text = response_text.strip()

    if response_text.startswith("```"):
        response_text = response_text.removeprefix(
            "```json"
        )
        response_text = response_text.removeprefix(
            "```"
        )
        response_text = response_text.removesuffix(
            "```"
        )
        response_text = response_text.strip()

    start = response_text.find("{")
    end = response_text.rfind("}")

    if start == -1 or end == -1 or start > end:
        raise RuntimeError(
            "Gemini returned invalid JSON for job requirements"
        )

    return response_text[start:end + 1]


def understand_job_requirements(
    description: str,
) -> list[dict]:
    """
    Understand job requirements using a hybrid strategy.

    Deterministic extraction provides high-confidence known
    requirements. Gemini identifies context, unknown requirements,
    importance, and richer requirement types.
    """

    deterministic = extract_deterministic_requirements(
        description
    )

    prompt = f"""
You are the job-requirement intelligence engine for ApplyIQ.

Analyze the following job description and extract the actual
candidate requirements.

JOB DESCRIPTION:

{description}

Return ONLY valid JSON.

Return exactly:

{{
  "requirements": [
    {{
      "requirement": "human-readable requirement name",
      "normalized_name": "canonical lowercase requirement name",
      "original_text": "exact or near-exact relevant wording",
      "context": "short surrounding context explaining the requirement",
      "requirement_type": "skill | experience | education | certification | domain | responsibility",
      "category": "technical | infrastructure | behavioral | domain | education | experience | general",
      "importance": "required | preferred | nice_to_have",
      "confidence": 0.0
    }}
  ]
}}

STRICT RULES:

1. Extract actual job requirements, not arbitrary nouns.
2. Extract technologies, frameworks, tools, engineering concepts,
   experience requirements, education requirements, certifications,
   and meaningful professional requirements.
3. Preserve the context in which a requirement appears.
4. Distinguish required requirements from preferred or nice-to-have
   requirements when the job description provides that distinction.
5. Do not invent requirements.
6. Do not infer a technology merely because another technology
   commonly uses it.
7. "Python" and "backend development using Python" should retain
   their relevant context.
8. Normalize aliases consistently.
9. Use lowercase for normalized_name.
10. Confidence must be between 0 and 1.
11. Return every meaningful requirement found.
12. Do not return duplicate normalized_name values.
13. Do not calculate candidate fit.
14. Do not evaluate whether the candidate possesses the requirement.
"""

    try:
        interaction = client.interactions.create(
            model="gemini-3.6-flash",
            input=prompt,
            generation_config={
                "thinking_level": "low",
            },
        )

        response_text = interaction.output_text

        if not response_text:
            raise RuntimeError(
                "Gemini returned empty job requirements"
            )

        parsed = json.loads(
            _clean_llm_json(response_text)
        )

        requirements = parsed.get(
            "requirements"
        )

        if not isinstance(
            requirements,
            list,
        ):
            raise RuntimeError(
                "Gemini requirements must be a list"
            )

    except Exception:
        # Deterministic extraction remains a safe fallback.
        return deterministic

    normalized_results = {}

    for item in requirements:

        if not isinstance(item, dict):
            continue

        requirement = str(
            item.get("requirement") or ""
        ).strip()

        if not requirement:
            continue

        normalized_name = normalize_requirement_name(
            str(
                item.get(
                    "normalized_name",
                    requirement,
                )
            )
        )

        if not normalized_name:
            continue

        confidence = item.get(
            "confidence",
            0.75,
        )

        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 0.75

        confidence = max(
            0.0,
            min(1.0, confidence),
        )

        normalized_results[normalized_name] = {
            "requirement": display_requirement_name(
                normalized_name
            ),
            "normalized_name": normalized_name,
            "original_text": (
                str(item.get("original_text") or "")
                .strip()
                or None
            ),
            "context": (
                str(item.get("context") or "")
                .strip()
                or None
            ),
            "requirement_type": (
                str(
                    item.get(
                        "requirement_type",
                        "skill",
                    )
                ).strip().lower()
            ),
            "category": (
                str(
                    item.get(
                        "category",
                        _infer_category(
                            normalized_name
                        ),
                    )
                ).strip().lower()
            ),
            "importance": (
                str(
                    item.get(
                        "importance",
                        "required",
                    )
                ).strip().lower()
            ),
            "confidence": confidence,
            "source": "llm",
        }

    # If Gemini omitted an obvious deterministic requirement,
    # retain the deterministic result.
    for item in deterministic:

        normalized_name = item[
            "normalized_name"
        ]

        if normalized_name not in normalized_results:
            normalized_results[
                normalized_name
            ] = item
        else:
            # Deterministic extraction increases confidence
            # when it independently confirms the same requirement.
            normalized_results[
                normalized_name
            ]["confidence"] = max(
                normalized_results[
                    normalized_name
                ]["confidence"],
                item["confidence"],
            )

            normalized_results[
                normalized_name
            ]["source"] = "hybrid"

            if not normalized_results[
                normalized_name
            ].get("context"):
                normalized_results[
                    normalized_name
                ]["context"] = item["context"]

    return list(
        normalized_results.values()
    )


def save_job_requirements(
    db: Session,
    job_id,
    requirements: list[dict],
) -> list[JobRequirement]:

    existing_requirements = (
        db.query(JobRequirement)
        .filter(
            JobRequirement.job_id == job_id
        )
        .all()
    )

    existing_by_name = {
        requirement.normalized_name: requirement
        for requirement in existing_requirements
    }

    saved_requirements = []

    for data in requirements:

        normalized_name = normalize_requirement_name(
            data["normalized_name"]
        )

        existing = existing_by_name.get(
            normalized_name
        )

        if existing:
            existing.requirement = data[
                "requirement"
            ]
            existing.original_text = data.get(
                "original_text"
            )
            existing.context = data.get(
                "context"
            )
            existing.requirement_type = data[
                "requirement_type"
            ]
            existing.category = data[
                "category"
            ]
            existing.importance = data[
                "importance"
            ]
            existing.confidence = data[
                "confidence"
            ]
            existing.source = data[
                "source"
            ]

            saved_requirements.append(existing)
            continue

        job_requirement = JobRequirement(
            job_id=job_id,
            requirement=data["requirement"],
            normalized_name=normalized_name,
            original_text=data.get(
                "original_text"
            ),
            context=data.get(
                "context"
            ),
            requirement_type=data[
                "requirement_type"
            ],
            category=data[
                "category"
            ],
            importance=data[
                "importance"
            ],
            confidence=data[
                "confidence"
            ],
            source=data[
                "source"
            ],
        )

        db.add(job_requirement)
        saved_requirements.append(
            job_requirement
        )

        existing_by_name[
            normalized_name
        ] = job_requirement

    db.commit()

    for requirement in saved_requirements:
        db.refresh(requirement)

    return saved_requirements

def extract_job_requirements(
    description: str,
) -> list[str]:
    """
    Backward-compatible requirement extraction for existing
    agent workflows.

    New intelligence flows should use understand_job_requirements() instead.
    """

    requirements = understand_job_requirements(
        description
    )

    return [
        item["requirement"]
        for item in requirements
    ]
