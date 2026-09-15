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

        fake_package = {
            "tailored_summary": "Python backend candidate with FastAPI experience.",
            "cover_letter": (
                "Dear Hiring Team,\n\n"
                "I am interested in the Python Backend Intern role.\n\n"
                "Sincerely,\n"
                "Anvi Sunil Pardhi"
            ),
            "key_strengths": [
                "Python backend development",
                "FastAPI development",
                "PostgreSQL experience",
            ],
            "application_questions": [
                {
                    "question": "Describe your Python experience.",
                    "answer": "I have used Python in backend development.",
                    "evidence_used": ["Python"],
                },
                {
                    "question": "Describe your FastAPI experience.",
                    "answer": "I have used FastAPI in backend projects.",
                    "evidence_used": ["FastAPI"],
                },
                {
                    "question": "Describe your database experience.",
                    "answer": "I have experience with PostgreSQL.",
                    "evidence_used": ["PostgreSQL"],
                },
            ],
        }

        def fake_generate(*args, **kwargs):
            return fake_package.copy()

        def fake_repair(*args, **kwargs):
            raise RuntimeError("Simulated Gemini quota failure")

        print("=" * 70)
        print("AI REPAIR FAILURE TEST")
        print("=" * 70)
        print()
        print("Gemini API will NOT be called.")
        print("Repair failure will be simulated locally.")
        print()

        with patch(
            "backend.app.services.application_package_service."
            "generate_complete_application_package",
            side_effect=fake_generate,
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
        print(f"Tailored summary  : {package['tailored_summary']}")
        print()
        print("Validation issues:")
        for issue in package["unsupported_claims"]:
            print(f"- {issue}")

        print()
        print("=" * 70)

        expected_issue = "AI repair unavailable: RuntimeError"

        if expected_issue in package["unsupported_claims"]:
            print("FAILURE HANDLING TEST PASSED")
        else:
            print("FAILURE HANDLING TEST FAILED")
            raise AssertionError(
                "Expected simulated AI repair failure was not recorded."
            )

    finally:
        db.close()


if __name__ == "__main__":
    main()
