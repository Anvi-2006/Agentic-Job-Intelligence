from backend.app.core.database import SessionLocal
from backend.app.models.job import Job


JOBS = [
    {
        "external_id": "DEMO-001",
        "title": "Backend Engineer Intern",
        "company": "Razorpay",
        "location": "Pune, India",
        "description": (
            "Looking for a backend engineering intern with experience "
            "in Python, FastAPI, REST APIs, PostgreSQL and problem solving."
        ),
        "source": "demo",
        "job_url": "https://example.com/jobs/backend-engineer-intern",
    },
    {
        "external_id": "DEMO-002",
        "title": "Python Backend Intern",
        "company": "FinTech Labs",
        "location": "Remote",
        "description": (
            "Seeking a Python backend intern with knowledge of Python, "
            "FastAPI, SQL, PostgreSQL and REST APIs."
        ),
        "source": "demo",
        "job_url": "https://example.com/jobs/python-backend-intern",
    },
    {
        "external_id": "DEMO-003",
        "title": "Software Engineer Intern",
        "company": "Google",
        "location": "Bangalore, India",
        "description": (
            "Software engineering internship requiring Python, "
            "databases, problem solving and software development skills."
        ),
        "source": "demo",
        "job_url": "https://example.com/jobs/software-engineer-intern",
    },
    {
        "external_id": "DEMO-004",
        "title": "AI Engineer Intern",
        "company": "AI Startup",
        "location": "Remote",
        "description": (
            "AI engineering intern with Python, machine learning, "
            "FastAPI and problem solving experience."
        ),
        "source": "demo",
        "job_url": "https://example.com/jobs/ai-engineer-intern",
    },
    {
        "external_id": "DEMO-005",
        "title": "Full Stack Developer Intern",
        "company": "Tech Solutions",
        "location": "Pune, India",
        "description": (
            "Full stack development internship requiring React, "
            "Python, REST APIs, databases and Git."
        ),
        "source": "demo",
        "job_url": "https://example.com/jobs/full-stack-intern",
    },
]


def seed_jobs():
    db = SessionLocal()

    try:
        for job_data in JOBS:
            existing_job = (
                db.query(Job)
                .filter(Job.external_id == job_data["external_id"])
                .first()
            )

            if existing_job:
                continue

            job = Job(**job_data)
            db.add(job)

        db.commit()

        print(f"Seeded {len(JOBS)} demo jobs.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_jobs()