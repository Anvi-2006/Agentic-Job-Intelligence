from backend.app.services.application_package_service import (
    _validate_generated_package,
)


def main():
    candidate_evidence = [
        {
            "evidence_id": "1",
            "category": "project",
            "title": "ResearchMind | Multi-Agent AI Research System",
            "content": (
                "Built a multi-agent AI research system using "
                "Python, LangChain, Groq, Tavily, BeautifulSoup, "
                "and Streamlit."
            ),
            "source": "resume",
        },
        {
            "evidence_id": "2",
            "category": "skill",
            "title": "Python",
            "content": (
                "Python used in backend development and "
                "agentic application projects."
            ),
            "source": "candidate_skill",
        },
        {
            "evidence_id": "3",
            "category": "skill",
            "title": "FastAPI",
            "content": (
                "FastAPI used for backend API development."
            ),
            "source": "candidate_skill",
        },
        {
            "evidence_id": "4",
            "category": "skill",
            "title": "PostgreSQL",
            "content": (
                "PostgreSQL used for persistent data storage."
            ),
            "source": "candidate_skill",
        },
    ]

    missing_requirements = []

    bad_package = {
        "cover_letter": (
            "Ihave built backend APIs using FastAPI and PostgreSQL.\n\n"
            "Sincerely,\n"
            "ResearchMind"
        ),
        "key_strengths": [
            "Python backend development",
            "Hands-on FastAPI experience",
            "PostgreSQL experience",
            "Ability to design large production systems",
        ],
        "application_questions": [
            {
                "question": "Canyou describe your Python experience?",
                "answer": "Ihave used Python for backend development.",
                "evidence_used": ["Python"],
            },
            {
                "question": "How have you used FastAPI?",
                "answer": "I have used FastAPI for backend API development.",
                "evidence_used": ["FastAPI"],
            },
            {
                "question": "What database experience do you have?",
                "answer": "I have used PostgreSQL for persistent data storage.",
                "evidence_used": ["PostgreSQL"],
            },
        ],
    }

    result = _validate_generated_package(
        ai_package=bad_package,
        tailored_summary=(
            "Detail-oriented candidate with experience "
            "building ResearchMind systems."
        ),
        evidence=candidate_evidence,
        missing_requirements=missing_requirements,
        candidate_name="Test Candidate",
    )

    print("VALID:", result["is_valid"])
    print("ISSUES:")

    for issue in result["issues"]:
        print("-", issue)


if __name__ == "__main__":
    main()