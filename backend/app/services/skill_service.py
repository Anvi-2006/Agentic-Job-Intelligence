from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models.skill import Skill, CandidateSkill
from backend.app.schemas.skill import SkillCreate, CandidateSkillCreate


def create_skill(db: Session, skill_data: SkillCreate) -> Skill:
    skill = Skill(
        name=skill_data.name
    )

    db.add(skill)
    db.commit()
    db.refresh(skill)

    return skill


def get_skill(db: Session, skill_id: UUID) -> Skill | None:
    return db.get(Skill, skill_id)


def add_skill_to_candidate(
    db: Session,
    candidate_id: UUID,
    skill_data: CandidateSkillCreate,
) -> CandidateSkill:

    candidate_skill = CandidateSkill(
        candidate_id=candidate_id,
        skill_id=skill_data.skill_id,
        proficiency=skill_data.proficiency,
    )

    db.add(candidate_skill)
    db.commit()
    db.refresh(candidate_skill)

    return candidate_skill


def get_candidate_skills(
    db: Session,
    candidate_id: UUID,
) -> list[CandidateSkill]:

    return (
        db.query(CandidateSkill)
        .filter(CandidateSkill.candidate_id == candidate_id)
        .all()
    )
