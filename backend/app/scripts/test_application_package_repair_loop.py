from backend.app.services.application_package_service import (
    MAX_REPAIR_ATTEMPTS,
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

    candidate_name = "Test Candidate"

    # ---------------------------------------------------------
    # Simulated first Gemini response: INVALID
    # ---------------------------------------------------------

    invalid_package = {
        "tailored_summary": (
            "Ihave backend experience and can design "
            "large production systems."
        ),
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
                "answer": (
                    "Ihave used Python for backend development."
                ),
                "evidence_used": ["Python"],
            },
            {
                "question": "How have you used FastAPI?",
                "answer": (
                    "I have used FastAPI for backend API development."
                ),
                "evidence_used": ["FastAPI"],
            },
            {
                "question": "What database experience do you have?",
                "answer": (
                    "I have used PostgreSQL for persistent data storage."
                ),
                "evidence_used": ["PostgreSQL"],
            },
        ],
    }

    # ---------------------------------------------------------
    # Simulated repaired Gemini response: VALID
    # ---------------------------------------------------------

    repaired_package = {
        "tailored_summary": (
            "Backend-focused candidate with experience using "
            "Python, FastAPI, and PostgreSQL, supported by "
            "multi-agent AI project development."
        ),
        "cover_letter": (
            "I have built backend APIs using FastAPI and PostgreSQL.\n\n"
            "Sincerely,\n"
            "Test Candidate"
        ),
        "key_strengths": [
            "Python backend development",
            "Hands-on FastAPI experience",
            "PostgreSQL experience",
            "Multi-agent AI research development",
        ],
        "application_questions": [
            {
                "question": "Can you describe your Python experience?",
                "answer": (
                    "I have used Python in backend development "
                    "and agentic application projects."
                ),
                "evidence_used": ["Python"],
            },
            {
                "question": "How have you used FastAPI?",
                "answer": (
                    "I have used FastAPI for backend API development."
                ),
                "evidence_used": ["FastAPI"],
            },
            {
                "question": "What database experience do you have?",
                "answer": (
                    "I have used PostgreSQL for persistent data storage."
                ),
                "evidence_used": ["PostgreSQL"],
            },
        ],
    }

    # ---------------------------------------------------------
    # Simulate the same repair-loop logic used by the service.
    # ---------------------------------------------------------

    ai_package = invalid_package
    repair_attempts = 0

    while repair_attempts < MAX_REPAIR_ATTEMPTS:

        validation_result = _validate_generated_package(
            ai_package=ai_package,
            evidence=candidate_evidence,
            missing_requirements=missing_requirements,
            candidate_name=candidate_name,
        )

        print(
            f"Attempt {repair_attempts}: "
            f"VALID = {validation_result['is_valid']}"
        )

        if validation_result["is_valid"]:
            break

        print("Validation issues:")

        for issue in validation_result["issues"]:
            print("-", issue)

        repair_attempts += 1

        # Simulate Gemini regeneration.
        ai_package = repaired_package

    # ---------------------------------------------------------
    # Final validation
    # ---------------------------------------------------------

    final_result = _validate_generated_package(
        ai_package=ai_package,
        evidence=candidate_evidence,
        missing_requirements=missing_requirements,
        candidate_name=candidate_name,
    )

    print()
    print("FINAL VALID:", final_result["is_valid"])
    print("REPAIR ATTEMPTS:", repair_attempts)
    print("FINAL ISSUES:", final_result["issues"])

    if final_result["is_valid"]:
        print()
        print("REPAIR LOOP TEST PASSED")
    else:
        print()
        print("REPAIR LOOP TEST FAILED")


if __name__ == "__main__":
    main()