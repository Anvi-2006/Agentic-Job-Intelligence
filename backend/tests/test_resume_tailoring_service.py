import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1])
)

from uuid import UUID

from backend.app.core.database import SessionLocal
from backend.app.services.resume_tailoring_service import generate_tailored_resume


CANDIDATE_ID = UUID(
    "332b3f24-eefc-4d05-99d5-56798d24a50c"
)

JOB_ID = UUID(
    "c0befb3f-90db-471d-82e4-39c33d213eaf"
)


def test_generate_tailored_resume():
    db = SessionLocal()

    try:
        result = generate_tailored_resume(
            db=db,
            candidate_id=CANDIDATE_ID,
            job_id=JOB_ID,
        )

        assert result["candidate_id"] == CANDIDATE_ID
        assert result["job_id"] == JOB_ID

        assert result["fit_score"] == 62.5

        assert "Problem Solving" in result[
            "missing_requirements"
        ]

        assert "Databases" in result[
            "partial_requirements"
        ]

        assert result["unsupported_claims"] == []
        assert result["is_valid"] is True

        assert result["summary"]
        assert len(result["evidence_used"]) > 0

        for evidence in result["evidence_used"]:
            assert evidence["evidence_id"]
            assert evidence["title"]

    finally:
        db.close()
