from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.application_package import (
    ApplicationPackageResponse,
)
from backend.app.services.application_package_query_service import (
    get_saved_application_package,
)
from backend.app.services.application_package_service import (
    generate_application_package,
)


router = APIRouter(
    prefix="/api/application-package",
    tags=["Application Package"],
)


@router.post(
    "/{candidate_id}/{job_id}/generate",
    response_model=ApplicationPackageResponse,
)
def generate_application_package_endpoint(
    candidate_id: UUID,
    job_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        package = generate_application_package(
            db=db,
            candidate_id=candidate_id,
            job_id=job_id,
        )

        return package

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Application package generation failed: {type(exc).__name__}",
        ) from exc


@router.get(
    "/{candidate_id}/{job_id}",
    response_model=ApplicationPackageResponse,
)
def get_application_package(
    candidate_id: UUID,
    job_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        return get_saved_application_package(
            db=db,
            candidate_id=candidate_id,
            job_id=job_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc