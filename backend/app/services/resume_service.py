from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models.resume import Resume
from backend.app.schemas.resume import ResumeCreate


def create_resume(
    db: Session,
    resume_data: ResumeCreate,
) -> Resume:
    resume = Resume(
        candidate_id=resume_data.candidate_id,
        file_name=resume_data.file_name,
        file_path=resume_data.file_path,
        raw_text=resume_data.raw_text,
    )

    db.add(resume)
    db.commit()
    db.refresh(resume)

    return resume


def get_resume(
    db: Session,
    resume_id: UUID,
) -> Resume | None:
    return db.get(Resume, resume_id)


def get_candidate_resumes(
    db: Session,
    candidate_id: UUID,
) -> list[Resume]:
    return (
        db.query(Resume)
        .filter(Resume.candidate_id == candidate_id)
        .all()
    )
