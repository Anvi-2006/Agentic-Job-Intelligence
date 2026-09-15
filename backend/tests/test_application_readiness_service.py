import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

from uuid import UUID

from backend.app.core.database import SessionLocal
from backend.app.services.application_readiness_service import (
    calculate_application_readiness,
)


CANDIDATE_ID = UUID(
    "332b3f24-eefc-4d05-99d5-56798d24a50c"
)

JOB_ID = UUID(
    "c0befb3f-90db-471d-82e4-39c33d213eaf"
)


def test_calculate_application_readiness():
    db = SessionLocal()

    try:
        result = calculate_application_readiness(
            db=db,
            candidate_id=CANDIDATE_ID,
            job_id=JOB_ID,
        )

        assert result["candidate_id"] == CANDIDATE_ID
        assert result["job_id"] == JOB_ID

        assert result["fit_score"] == 62.5

        assert result["readiness_score"] == 64.5
        assert result["readiness_level"] == "review"
        assert result["recommendation"] == "REVIEW"

        assert result["matched_requirements"] == 2

        assert "Databases" in result["partial_requirements"]

        assert "Problem Solving" in result["missing_requirements"]

        assert result["evidence_count"] > 0

        assert len(result["reasons"]) > 0

    finally:
        db.close()
