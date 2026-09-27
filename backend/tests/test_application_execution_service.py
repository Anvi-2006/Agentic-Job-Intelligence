from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from backend.app.services.application_execution_service import (
    mark_execution_failed,
    mark_execution_submitted,
    retry_failed_execution,
)


def test_submission_requires_explicit_human_approval():
    db = MagicMock()

    execution = SimpleNamespace(
        id=uuid4(),
        application_id=uuid4(),
        status="executing",
        current_step=3,
        current_action="browser_fields_completed",
        submission_approved=False,
        failure_reason=None,
        started_at=None,
        completed_at=None,
        created_at=None,
        updated_at=None,
    )

    db.query.return_value.filter.return_value.first.return_value = execution

    with pytest.raises(
        ValueError,
        match="explicit human approval",
    ):
        mark_execution_submitted(
            db=db,
            application_id=execution.application_id,
        )

    db.commit.assert_not_called()


def test_failed_execution_clears_submission_approval():
    db = MagicMock()

    execution = SimpleNamespace(
        id=uuid4(),
        application_id=uuid4(),
        status="executing",
        current_step=4,
        current_action="submission_approved",
        submission_approved=True,
        failure_reason=None,
        started_at=None,
        completed_at=None,
        created_at=None,
        updated_at=None,
    )

    db.query.return_value.filter.return_value.first.return_value = execution

    result = mark_execution_failed(
        db=db,
        application_id=execution.application_id,
        failure_reason="Browser session failed.",
    )

    assert result["status"] == "failed"
    assert result["submission_approved"] is False
    assert result["failure_reason"] == "Browser session failed."
    db.commit.assert_called_once()


def test_retry_failed_execution_requires_fresh_submission_approval():
    db = MagicMock()

    execution = SimpleNamespace(
        id=uuid4(),
        application_id=uuid4(),
        status="failed",
        current_step=4,
        current_action="failed",
        submission_approved=False,
        failure_reason="Browser session failed.",
        started_at=None,
        completed_at="completed",
        created_at=None,
        updated_at=None,
    )

    db.query.return_value.filter.return_value.first.return_value = execution

    result = retry_failed_execution(
        db=db,
        application_id=execution.application_id,
    )

    assert result["status"] == "ready"
    assert result["current_action"] == "retry_ready"
    assert result["submission_approved"] is False
    assert result["failure_reason"] is None
    assert result["completed_at"] is None
    db.commit.assert_called_once()
