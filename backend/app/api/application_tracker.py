from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.services.application_tracker_service import (
    get_candidate_applications,
)

router = APIRouter(
    prefix="/api/applications",
    tags=["Application Tracker"],
)


@router.get("/{candidate_id}")
def get_application_tracker(
    candidate_id: UUID,
    db: Session = Depends(get_db),
):
    applications = get_candidate_applications(
        db=db,
        candidate_id=candidate_id,
    )

    return {
        "candidate_id": str(candidate_id),
        "total_applications": len(applications),
        "applications": applications,
    }