from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models.education import Education
from backend.app.schemas.education import EducationCreate


def create_education(
    db: Session,
    education_data: EducationCreate,
) -> Education:
    education = Education(
        candidate_id=education_data.candidate_id,
        institution=education_data.institution,
        degree=education_data.degree,
        field_of_study=education_data.field_of_study,
        start_year=education_data.start_year,
        end_year=education_data.end_year,
    )

    db.add(education)
    db.commit()
    db.refresh(education)

    return education


def get_education(
    db: Session,
    education_id: UUID,
) -> Education | None:
    return db.get(Education, education_id)


def get_candidate_education(
    db: Session,
    candidate_id: UUID,
) -> list[Education]:
    return (
        db.query(Education)
        .filter(Education.candidate_id == candidate_id)
        .all()
    )
