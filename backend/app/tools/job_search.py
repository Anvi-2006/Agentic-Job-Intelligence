from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models.job import Job


def search_jobs(
    db: Session,
    keywords: str | None = None,
    location: str | None = None,
) -> list[dict]:
    """
    Search jobs stored in the database.

    The tool supports optional keyword and location filters.
    """

    query = db.query(Job)

    if keywords:
        keyword_list = [
            word.strip().lower()
            for word in keywords.split()
            if word.strip()
        ]

        conditions = []

        for keyword in keyword_list:
            conditions.append(
                Job.title.ilike(f"%{keyword}%")
                | Job.description.ilike(f"%{keyword}%")
                | Job.company.ilike(f"%{keyword}%")
            )

        if conditions:
            from sqlalchemy import or_

            query = query.filter(or_(*conditions))

    if location:
        query = query.filter(
            Job.location.ilike(f"%{location.strip()}%")
        )

    jobs = query.order_by(
        Job.company.asc(),
        Job.title.asc(),
    ).all()

    return [
        {
            "job_id": str(job.id),
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "description": job.description,
            "source": job.source,
            "job_url": job.job_url,
        }
        for job in jobs
    ]