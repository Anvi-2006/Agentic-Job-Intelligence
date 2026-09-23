import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1])
)

from uuid import UUID

from backend.app.core.database import SessionLocal
from backend.app.services import resume_tailoring_service


CANDIDATE_ID = UUID(
    "332b3f24-eefc-4d05-99d5-56798d24a50c"
)

JOB_ID = UUID(
    "c0befb3f-90db-471d-82e4-39c33d213eaf"
)


def test_generate_tailored_resume(monkeypatch):
    db = SessionLocal()

    try:
        monkeypatch.setattr(
            resume_tailoring_service,
            "calculate_job_fit_score",
            lambda **kwargs: {
                "score": 60.0,
                "matches": [
                    {
                        "requirement": "Python",
                        "match_status": "matched",
                        "evidence_ids": [
                            "11111111-1111-1111-1111-111111111111"
                        ],
                    },
                    {
                        "requirement": "React",
                        "match_status": "matched",
                        "evidence_ids": [
                            "22222222-2222-2222-2222-222222222222"
                        ],
                    },
                    {
                        "requirement": "Databases",
                        "match_status": "partial",
                        "evidence_ids": [
                            "33333333-3333-3333-3333-333333333333"
                        ],
                    },
                    {
                        "requirement": "Problem Solving",
                        "match_status": "partial",
                        "evidence_ids": [
                            "44444444-4444-4444-4444-444444444444"
                        ],
                    },
                    {
                        "requirement": "Software Engineering",
                        "match_status": "missing",
                        "evidence_ids": [],
                    },
                ],
                "missing_requirements": [
                    "Software Engineering"
                ],
                "partial_requirements": [
                    "Databases",
                    "Problem Solving",
                ],
            },
        )

        monkeypatch.setattr(
            resume_tailoring_service,
            "extract_job_requirements",
            lambda description: [
                "Python",
                "React",
                "Databases",
                "Problem Solving",
                "Software Engineering",
            ],
        )

        evidence = [
            {
                "evidence_id": "11111111-1111-1111-1111-111111111111",
                "category": "skill",
                "title": "Python",
                "content": "Python development experience.",
                "source": "candidate_skill",
            },
            {
                "evidence_id": "22222222-2222-2222-2222-222222222222",
                "category": "skill",
                "title": "React",
                "content": "React development experience.",
                "source": "candidate_skill",
            },
        ]

        monkeypatch.setattr(
            resume_tailoring_service,
            "select_application_evidence",
            lambda **kwargs: evidence,
        )

        monkeypatch.setattr(
            resume_tailoring_service,
            "generate_resume_tailoring",
            lambda **kwargs: (
                "Third-year IT student with verified experience "
                "in Python and React development."
            ),
        )

        monkeypatch.setattr(
            resume_tailoring_service,
            "validate_generated_summary",
            lambda **kwargs: {
                "unsupported_claims": [],
                "is_valid": True,
            },
        )

        result = resume_tailoring_service.generate_tailored_resume(
            db=db,
            candidate_id=CANDIDATE_ID,
            job_id=JOB_ID,
        )

        assert result["candidate_id"] == CANDIDATE_ID
        assert result["job_id"] == JOB_ID

        assert result["fit_score"] == 60.0

        assert "Problem Solving" in result[
            "partial_requirements"
        ]

        assert "Databases" in result[
            "partial_requirements"
        ]

        assert "Software Engineering" in result[
            "missing_requirements"
        ]

        assert result["unsupported_claims"] == []
        assert result["is_valid"] is True

        assert result["summary"]

        assert len(result["evidence_used"]) == 2

        for evidence_item in result["evidence_used"]:
            assert evidence_item["evidence_id"]
            assert evidence_item["title"]

    finally:
        db.close()