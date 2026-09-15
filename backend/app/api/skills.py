from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.skill import (
    SkillCreate,
    SkillResponse,
    CandidateSkillCreate,
    CandidateSkillResponse,
)
from backend.app.services.skill_service import (
    create_skill,
    get_skill,
    add_skill_to_candidate,
    get_candidate_skills,
)

router = APIRouter(prefix="/api/skills", tags=["Skills"])


@router.post("", response_model=SkillResponse, status_code=201)
def create_skill_endpoint(
    skill_data: SkillCreate,
    db: Session = Depends(get_db),
):
    return create_skill(db, skill_data)


@router.get("/{skill_id}", response_model=SkillResponse)
def get_skill_endpoint(
    skill_id: UUID,
    db: Session = Depends(get_db),
):
    skill = get_skill(db, skill_id)

    if skill is None:
        raise HTTPException(
            status_code=404,
            detail="Skill not found",
        )

    return skill


@router.post(
    "/candidate/{candidate_id}",
    response_model=CandidateSkillResponse,
    status_code=201,
)
def add_skill_to_candidate_endpoint(
    candidate_id: UUID,
    skill_data: CandidateSkillCreate,
    db: Session = Depends(get_db),
):
    return add_skill_to_candidate(
        db,
        candidate_id,
        skill_data,
    )


@router.get(
    "/candidate/{candidate_id}",
    response_model=list[CandidateSkillResponse],
)
def get_candidate_skills_endpoint(
    candidate_id: UUID,
    db: Session = Depends(get_db),
):
    return get_candidate_skills(db, candidate_id)
