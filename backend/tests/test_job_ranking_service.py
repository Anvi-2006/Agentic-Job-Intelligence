import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

from uuid import UUID

import pytest

from backend.app.core.database import SessionLocal
from backend.app.models.job import Job
from backend.app.services import job_ranking_service


CANDIDATE_ID = UUID(
    "332b3f24-eefc-4d05-99d5-56798d24a50c"
)

JOB_A_ID = UUID(
    "c0befb3f-90db-471d-82e4-39c33d213eaf"
)

JOB_B_ID = UUID(
    "3460f57b-3340-4680-8c59-d28c33126d42"
)


def _fit_result(score):
    return {
        "score": score,
        "matches": [
            {
                "requirement": "Python",
                "match_status": "matched",
            }
        ],
        "matched_requirements": 1,
        "total_requirements": 1,
        "missing_requirements": [],
        "partial_requirements": [],
    }


def test_rank_jobs_for_candidate_orders_by_fit_score(monkeypatch):
    db = SessionLocal()

    try:
        def fake_fit_score(**kwargs):
            if kwargs["job_id"] == JOB_A_ID:
                return _fit_result(70.0)

            if kwargs["job_id"] == JOB_B_ID:
                return _fit_result(90.0)

            raise AssertionError(
                f"Unexpected job ID: {kwargs['job_id']}"
            )

        monkeypatch.setattr(
            job_ranking_service,
            "calculate_job_fit_score",
            fake_fit_score,
        )

        result = job_ranking_service.rank_jobs_for_candidate(
            db=db,
            candidate_id=CANDIDATE_ID,
            job_ids=[
                str(JOB_A_ID),
                str(JOB_B_ID),
            ],
        )

        assert len(result) == 2
        assert result[0]["job_id"] == str(JOB_B_ID)
        assert result[0]["fit_score"] == 90.0
        assert result[1]["job_id"] == str(JOB_A_ID)
        assert result[1]["fit_score"] == 70.0

    finally:
        db.close()


def test_rank_jobs_for_candidate_deduplicates_job_ids(monkeypatch):
    db = SessionLocal()

    try:
        calls = []

        def fake_fit_score(**kwargs):
            calls.append(kwargs["job_id"])
            return _fit_result(80.0)

        monkeypatch.setattr(
            job_ranking_service,
            "calculate_job_fit_score",
            fake_fit_score,
        )

        result = job_ranking_service.rank_jobs_for_candidate(
            db=db,
            candidate_id=CANDIDATE_ID,
            job_ids=[
                str(JOB_A_ID),
                str(JOB_A_ID),
            ],
        )

        assert len(result) == 1
        assert result[0]["job_id"] == str(JOB_A_ID)
        assert calls == [JOB_A_ID]

    finally:
        db.close()


def test_rank_jobs_for_candidate_rejects_missing_job():
    db = SessionLocal()

    missing_job_id = UUID(
        "11111111-1111-1111-1111-111111111111"
    )

    try:
        with pytest.raises(
            ValueError,
            match="Jobs not found",
        ):
            job_ranking_service.rank_jobs_for_candidate(
                db=db,
                candidate_id=CANDIDATE_ID,
                job_ids=[
                    str(JOB_A_ID),
                    str(missing_job_id),
                ],
            )
    finally:
        db.close()


def test_rank_jobs_for_candidate_returns_empty_for_no_jobs():
    db = SessionLocal()

    try:
        result = job_ranking_service.rank_jobs_for_candidate(
            db=db,
            candidate_id=CANDIDATE_ID,
            job_ids=[],
        )

        assert result == []

    finally:
        db.close()
