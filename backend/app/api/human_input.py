from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.core.database import SessionLocal
from backend.app.services.human_input_service import (
    answer_human_input_request,
    get_pending_human_input_requests,
)


router = APIRouter(
    prefix="/api/executions",
    tags=["Human Input"],
)


class HumanInputAnswerRequest(BaseModel):
    answer: str


@router.get(
    "/{execution_id}/human-input",
)
def get_human_input_endpoint(
    execution_id: UUID,
):
    db = SessionLocal()

    try:
        return get_pending_human_input_requests(
            db=db,
            execution_id=execution_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    finally:
        db.close()


@router.post(
    "/human-input/{request_id}/answer",
)
def answer_human_input_endpoint(
    request_id: UUID,
    request: HumanInputAnswerRequest,
):
    db = SessionLocal()

    try:
        return answer_human_input_request(
            db=db,
            request_id=request_id,
            answer=request.answer,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    finally:
        db.close()