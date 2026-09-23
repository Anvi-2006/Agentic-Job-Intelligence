from unittest.mock import patch

from backend.app.core.database import SessionLocal
from backend.app.models.candidate import CandidateProfile
from backend.app.models.job import Job
from backend.app.models.user import User
from backend.app.services.application_package_service import (
    generate_application_package,
)


def main():
    db = SessionLocal()

    try:
        candidate = db.query(CandidateProfile).first()

        if candidate is None:
            raise RuntimeError("No candidate profile found.")

        user = (
            db.query(User)
            .filter(User.id == candidate.user_id)
            .first()
        )

        if user is None:
            raise RuntimeError("Candidate user not found.")

        candidate_name = user.full_name

        job = (
            db.query(Job)
            .filter(Job.company == "FinTech Labs")
            .first()
        )

        if job is None:
            raise RuntimeError("FinTech Labs job not found.")

        invalid_package = {
            "tailored_summary": (
                "Python backend candidate with experience building "
                "backend applications."
            ),
            "cover_letter": (
                "Dear Hiring Team,\n\n"
                "I am interested in the Python Backend Intern role.\n\n"
                "Sincerely,\n"
                "Wrong Name"
            ),
            "key_strengths": [
                "Python backend development",
                "FastAPI development",
                "Ability to design large production systems",
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
                    "question": "Describe your database experience.",
                    "answer": (
                        "I have used PostgreSQL for persistent "
                        "data storage."
                    ),
                    "evidence_used": ["PostgreSQL"],
                },
            ],
        }

        repaired_package = {
            "tailored_summary": (
                "Python backend candidate with experience building "
                "backend applications using FastAPI."
            ),
            "cover_letter": (
                "Dear Hiring Team,\n\n"
                "I am interested in the Python Backend Intern role. "
                "I have used Python and FastAPI in backend projects.\n\n"
                "Sincerely,\n"
                f"{candidate_name}"
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
                    "question": "Describe your database experience.",
                    "answer": (
                        "I have used PostgreSQL for persistent "
                        "data storage."
                    ),
                    "evidence_used": ["PostgreSQL"],
                },
            ],
        }

        repair_calls = []

        def fake_repair(*args, **kwargs):
            repair_calls.append(kwargs)
            return repaired_package.copy()

        print("=" * 70)
        print("AI REPAIR SUCCESS TEST")
        print("=" * 70)
        print()
        print("Gemini API will NOT be called.")
        print("A deterministic invalid package will be repaired locally.")
        print()

        with patch(
            "backend.app.services.application_package_service."
            "generate_complete_application_package",
            return_value=invalid_package,
        ), patch(
            "backend.app.services.application_package_service."
            "regenerate_application_package",
            side_effect=fake_repair,
        ):
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
        print(f"Repair calls      : {len(repair_calls)}")
        print()
        print("Validation issues:")

        if package["unsupported_claims"]:
            for issue in package["unsupported_claims"]:
                print(f"- {issue}")
        else:
            print("None")

        print()
        print("=" * 70)

        assert len(repair_calls) >= 1
        assert package["is_valid"] is True
        assert package["unsupported_claims"] == []
        assert len(package["key_strengths"]) == 3
        assert len(package["application_questions"]) == 3

        print("SUCCESSFUL REPAIR TEST PASSED")

    finally:
        db.close()


if __name__ == "__main__":
    main()