from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models.application_execution import ApplicationExecution
from backend.app.models.human_input_request import (
    HumanInputRequest,
    HUMAN_INPUT_STATUS_ANSWERED,
    HUMAN_INPUT_STATUS_PENDING,
)


def create_human_input_request(
    db: Session,
    execution_id: UUID,
    field_name: str,
    question: str,
) -> dict:
    execution = db.get(
        ApplicationExecution,
        execution_id,
    )

    if execution is None:
        raise ValueError(
            "Application execution not found."
        )

    if not field_name.strip():
        raise ValueError(
            "Human input field name cannot be empty."
        )

    if not question.strip():
        raise ValueError(
            "Human input question cannot be empty."
        )

    existing = (
        db.query(HumanInputRequest)
        .filter(
            HumanInputRequest.execution_id == execution_id,
            HumanInputRequest.field_name == field_name.strip(),
            HumanInputRequest.status
            == HUMAN_INPUT_STATUS_PENDING,
        )
        .first()
    )

    if existing is not None:
        return _human_input_response(existing)

    request = HumanInputRequest(
        execution_id=execution_id,
        field_name=field_name.strip(),
        question=question.strip(),
        status=HUMAN_INPUT_STATUS_PENDING,
    )

    db.add(request)
    db.commit()
    db.refresh(request)

    return _human_input_response(request)


def get_pending_human_input_requests(
    db: Session,
    execution_id: UUID,
) -> list[dict]:
    execution = db.get(
        ApplicationExecution,
        execution_id,
    )

    if execution is None:
        raise ValueError(
            "Application execution not found."
        )

    requests = (
        db.query(HumanInputRequest)
        .filter(
            HumanInputRequest.execution_id == execution_id,
            HumanInputRequest.status
            == HUMAN_INPUT_STATUS_PENDING,
        )
        .order_by(
            HumanInputRequest.created_at.asc(),
            HumanInputRequest.id.asc(),
        )
        .all()
    )

    return [
        _human_input_response(request)
        for request in requests
    ]


def answer_human_input_request(
    db: Session,
    request_id: UUID,
    answer: str,
) -> dict:
    request = db.get(
        HumanInputRequest,
        request_id,
    )

    if request is None:
        raise ValueError(
            "Human input request not found."
        )

    if request.status != HUMAN_INPUT_STATUS_PENDING:
        raise ValueError(
            "Human input request has already been answered."
        )

    if not answer.strip():
        raise ValueError(
            "Human input answer cannot be empty."
        )

    request.answer = answer.strip()
    request.status = HUMAN_INPUT_STATUS_ANSWERED
    request.answered_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(request)

    return _human_input_response(request)

def get_answered_human_input_requests(
    db: Session,
    execution_id: UUID,
) -> list[dict]:
    execution = db.get(
        ApplicationExecution,
        execution_id,
    )

    if execution is None:
        raise ValueError(
            "Application execution not found."
        )

    requests = (
        db.query(HumanInputRequest)
        .filter(
            HumanInputRequest.execution_id == execution_id,
            HumanInputRequest.status
            == HUMAN_INPUT_STATUS_ANSWERED,
        )
        .order_by(
            HumanInputRequest.answered_at.asc(),
            HumanInputRequest.id.asc(),
        )
        .all()
    )

    return [
        _human_input_response(request)
        for request in requests
    ]


def _human_input_response(
    request: HumanInputRequest,
) -> dict:
    return {
        "request_id": str(request.id),
        "execution_id": str(request.execution_id),
        "field_name": request.field_name,
        "question": request.question,
        "status": request.status,
        "answer": request.answer,
        "created_at": request.created_at,
        "answered_at": request.answered_at,
        "updated_at": request.updated_at,
    }