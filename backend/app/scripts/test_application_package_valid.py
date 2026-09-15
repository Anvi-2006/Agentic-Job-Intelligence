from unittest.mock import patch

from backend.app.core.database import SessionLocal
from backend.app.models.candidate import CandidateProfile
from backend.app.models.job import Job
from backend.app.services.application_package_service import (
    generate_application_package,
)


def main():
    db = SessionLocal()

    try:
        candidate = db.query(CandidateProfile).first()

        if candidate is None:
            raise RuntimeError("No candidate profile found.")

        job = (
            db.query(Job)
            .filter(Job.company == "FinTech Labs")
            .first()
        )

        if job is None:
            raise RuntimeError("FinTech Labs job not found.")

        valid_package = {
            "tailored_summary": (
                "Python backend candidate with experience building "
                "backend and multi-agent applications using FastAPI."
            ),
            "cover_letter": (
                "Dear Hiring Team,\n\n"
                "I am interested in the Python Backend Intern role. "
                "I have used Python and FastAPI in backend projects "
                "and have built multi-agent applications.\n\n"
                "Sincerely,\n"
                "Anvi"
            ),
            "key_strengths": [
                "Python backend development",
                "FastAPI development",
                "PostgreSQL experience",
            ],
            "application_questions": [
                {
                    "question": "Describe your Python experience.",
                    "answer": (
                        "I have used Python in backend development "
                        "and agentic application projects."
                    ),
                    "evidence_used": ["Python"],
                },
                {
                    "question": "Describe your FastAPI experience.",
                    "answer": (
                        "I have used FastAPI in backend development "
                        "projects."
                    ),
                    "evidence_used": ["FastAPI"],
                },
                {
                    "question": "Describe a project you built.",
                    "answer": (
                        "I built ResearchMind, a multi-agent AI "
                        "research system using Python and related AI tools."
                    ),
                    "evidence_used": ["ResearchMind | Multi-Agent AI Research System"],
                },
            ],
        }

        print("=" * 70)
        print("VALID APPLICATION PACKAGE TEST")
        print("=" * 70)
        print()
        print("Gemini API will NOT be called.")
        print("A deterministic valid package will be supplied.")
        print()

        def unexpected_repair(*args, **kwargs):
            raise AssertionError(
                "Initial package failed validation. "
                "The repair function was called unexpectedly."
            )

        with patch(
            "backend.app.services.application_package_service."
            "generate_complete_application_package",
            return_value=valid_package,
        ), patch(
            "backend.app.services.application_package_service."
            "regenerate_application_package",
            side_effect=unexpected_repair,
        ) as mock_repair:

            package = generate_application_package(
                db=db,
                candidate_id=candidate.id,
                job_id=job.id,
            )

        print("RESULT")
        print("-" * 70)
        print(f"Valid             : {package['is_valid']}")
        print(f"Recommendation    : {package['recommendation']}")
        print(f"Readiness score   : {package['readiness_score']}")
        print()

        print("Validation issues:")
        if package["unsupported_claims"]:
            for issue in package["unsupported_claims"]:
                print(f"- {issue}")
        else:
            print("None")

        print()
        print(f"Repair called     : {mock_repair.called}")
        print(f"Strength count    : {len(package['key_strengths'])}")
        print(
            f"Question count    : "
            f"{len(package['application_questions'])}"
        )
        print()

        print("=" * 70)

        assert package["is_valid"] is True
        assert package["unsupported_claims"] == []
        assert len(package["key_strengths"]) == 3
        assert len(package["application_questions"]) == 3
        assert mock_repair.called is False

        print("VALID PACKAGE TEST PASSED")

    finally:
        db.close()


if __name__ == "__main__":
    main()
