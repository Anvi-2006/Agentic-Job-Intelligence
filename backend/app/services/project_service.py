from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models.project import Project
from backend.app.schemas.project import ProjectCreate


def create_project(
    db: Session,
    project_data: ProjectCreate,
) -> Project:
    project = Project(
        candidate_id=project_data.candidate_id,
        name=project_data.name,
        description=project_data.description,
        technologies=project_data.technologies,
        github_url=project_data.github_url,
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return project


def get_project(
    db: Session,
    project_id: UUID,
) -> Project | None:
    return db.get(Project, project_id)


def get_candidate_projects(
    db: Session,
    candidate_id: UUID,
) -> list[Project]:
    return (
        db.query(Project)
        .filter(Project.candidate_id == candidate_id)
        .all()
    )
