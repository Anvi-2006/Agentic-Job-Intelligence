from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.core.database import SessionLocal
from backend.app.main import app
from backend.app.models.candidate import CandidateProfile
from backend.app.models.job import Job


client = TestClient(app)


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

        candidate_id = str(candidate.id)
        job_id = str(job.id)

        valid_package = {
            "candidate_id": candidate.id,
            "job_id": job.id,
            "company": job.company,
            "job_title": job.title,
            "readiness_score": 85.0,
            "recommendation": "APPLY",
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
            "missing_requirements": [],
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
                    "evidence_used": [
                        "ResearchMind | Multi-Agent AI Research System"
                    ],
                },
            ],
            "evidence_used": [
                "ResearchMind | Multi-Agent AI Research System",
                "Python",
                "FastAPI",
                "PostgreSQL",
            ],
            "unsupported_claims": [],
            "is_valid": True,
        }

        print("=" * 70)
        print("APPLICATION PACKAGE API TEST")
        print("=" * 70)
        print()
        print("Gemini API will NOT be called.")
        print("A deterministic valid package will be supplied.")
        print()

        with patch(
            "backend.app.api.application_package."
            "generate_application_package",
            return_value=valid_package,
        ) as mock_generate:

            response = client.post(
                f"/api/application-package/{candidate_id}/{job_id}/generate"
            )

        print("GENERATE ENDPOINT")
        print("-" * 70)
        print("Status code       :", response.status_code)
        print("Generate called    :", mock_generate.called)

        assert response.status_code == 200, response.text

        data = response.json()

        assert data["candidate_id"] == candidate_id
        assert data["job_id"] == job_id
        assert data["company"] == "FinTech Labs"
        assert data["recommendation"] == "APPLY"
        assert data["readiness_score"] == 85.0
        assert data["is_valid"] is True
        assert len(data["key_strengths"]) == 3
        assert len(data["application_questions"]) == 3

        print("Response valid     : True")
        print()

        response = client.get(
            f"/api/application-package/{candidate_id}/{job_id}"
        )

        print("GET ENDPOINT")
        print("-" * 70)
        print("Status code       :", response.status_code)

        assert response.status_code == 200, response.text

        saved_data = response.json()

        assert saved_data["candidate_id"] == candidate_id
        assert saved_data["job_id"] == job_id
        assert saved_data["company"] == "FinTech Labs"
        assert saved_data["recommendation"] == "APPLY"
        assert saved_data["is_valid"] is True

        print("Saved package valid: True")
        print()
        print("=" * 70)
        print("APPLICATION PACKAGE API TEST PASSED")
        print("=" * 70)

    finally:
        db.close()


if __name__ == "__main__":
    main()