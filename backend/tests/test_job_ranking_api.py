from uuid import UUID

from fastapi.testclient import TestClient

from backend.app.api import job_ranking as job_ranking_api
from backend.app.main import app


CANDIDATE_ID = "332b3f24-eefc-4d05-99d5-56798d24a50c"
JOB_A = "c0befb3f-90db-471d-82e4-39c33d213eaf"
JOB_B = "3460f57b-3340-4680-8c59-d28c33126d42"


def test_job_ranking_endpoint_returns_ranked_jobs(monkeypatch):
    def fake_rank_jobs_for_candidate(db, candidate_id, job_ids):
        assert candidate_id == UUID(CANDIDATE_ID)
        assert job_ids == [JOB_A, JOB_B]

        return [
            {
                "job_id": JOB_A,
                "title": "Software Engineer Intern",
                "company": "Microsoft",
                "location": "Bangalore, India",
                "job_url": "https://example.com/jobs/demo-001",
                "fit_score": 70.0,
                "recommendation": "good_match",
                "recommendation_reason": "Strong match on Python.",
                "matched_requirements": 2,
                "total_requirements": 5,
                "missing_requirements": [],
                "partial_requirements": ["Problem Solving"],
            },
            {
                "job_id": JOB_B,
                "title": "Backend Engineer Intern",
                "company": "Razorpay",
                "location": "Pune, India",
                "job_url": "https://example.com/jobs/backend-engineer-intern",
                "fit_score": 80.0,
                "recommendation": "good_match",
                "recommendation_reason": "Strong match on Python.",
                "matched_requirements": 3,
                "total_requirements": 5,
                "missing_requirements": [],
                "partial_requirements": ["REST APIs"],
            },
        ]

    monkeypatch.setattr(
        job_ranking_api,
        "rank_jobs_for_candidate",
        fake_rank_jobs_for_candidate,
    )

    client = TestClient(app)

    response = client.post(
        f"/api/job-ranking/{CANDIDATE_ID}",
        json={"job_ids": [JOB_A, JOB_B]},
    )

    assert response.status_code == 200

    body = response.json()

    assert body["candidate_id"] == CANDIDATE_ID
    assert len(body["jobs"]) == 2
    assert body["jobs"][0]["job_id"] == JOB_A
    assert body["jobs"][1]["job_id"] == JOB_B


def test_job_ranking_endpoint_returns_404_for_missing_job(monkeypatch):
    def fake_rank_jobs_for_candidate(db, candidate_id, job_ids):
        raise ValueError(f"Jobs not found: {JOB_B}")

    monkeypatch.setattr(
        job_ranking_api,
        "rank_jobs_for_candidate",
        fake_rank_jobs_for_candidate,
    )

    client = TestClient(app)

    response = client.post(
        f"/api/job-ranking/{CANDIDATE_ID}",
        json={"job_ids": [JOB_B]},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == f"Jobs not found: {JOB_B}"


def test_job_ranking_endpoint_rejects_empty_job_ids():
    client = TestClient(app)

    response = client.post(
        f"/api/job-ranking/{CANDIDATE_ID}",
        json={"job_ids": []},
    )

    assert response.status_code == 422


def test_job_ranking_endpoint_rejects_invalid_candidate_id():
    client = TestClient(app)

    response = client.post(
        "/api/job-ranking/not-a-uuid",
        json={"job_ids": [JOB_A]},
    )

    assert response.status_code == 422
