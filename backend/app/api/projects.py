from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.project import ProjectCreate, ProjectResponse
from backend.app.services.project_service import (
    create_project,
    get_project,
    get_candidate_projects,
)


router = APIRouter(
    prefix="/api/projects",
    tags=["Projects"],
)


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=201,
)
def create_project_endpoint(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
):
    return create_project(db, project_data)


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
)
def get_project_endpoint(
    project_id: UUID,
    db: Session = Depends(get_db),
):
    project = get_project(db, project_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    return project


@router.get(
    "/candidate/{candidate_id}",
    response_model=list[ProjectResponse],
)
def get_candidate_projects_endpoint(
    candidate_id: UUID,
    db: Session = Depends(get_db),
):
    return get_candidate_projects(db, candidate_id)
