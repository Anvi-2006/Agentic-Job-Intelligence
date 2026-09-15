from sqlalchemy.orm import Session

from backend.app.models.candidate import CandidateProfile
from backend.app.schemas.candidate import CandidateCreate


def create_candidate(
    db: Session,
    candidate_data: CandidateCreate,
) -> CandidateProfile:

    candidate = CandidateProfile(
        user_id=candidate_data.user_id,
        headline=candidate_data.headline,
        summary=candidate_data.summary,
        preferred_roles=candidate_data.preferred_roles,
        preferred_locations=candidate_data.preferred_locations,
    )

    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    return candidate


def get_candidate(
    db: Session,
    candidate_id,
) -> CandidateProfile | None:

    return db.get(CandidateProfile, candidate_id)