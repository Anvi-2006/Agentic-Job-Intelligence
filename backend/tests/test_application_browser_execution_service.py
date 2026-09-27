from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

from backend.app.services.application_browser_execution_service import (
    execute_application_browser_step,
)


def test_browser_execution_marks_execution_failed_on_unexpected_error():
    db = MagicMock()

    execution = SimpleNamespace(
        id=uuid4(),
        application_id=uuid4(),
        status="executing",
        current_step=2,
        current_action="browser_fields_completed",
        submission_approved=False,
        failure_reason=None,
    )

    db.query.return_value.filter.return_value.first.return_value = execution

    with patch(
        "backend.app.services.application_browser_execution_service.SessionLocal",
        return_value=db,
    ), patch(
        "backend.app.services.application_browser_execution_service.build_application_data",
        side_effect=RuntimeError("Browser crashed."),
    ), patch(
        "backend.app.services.application_browser_execution_service.mark_execution_failed",
    ) as mock_mark_failed:
        try:
            execute_application_browser_step(
                application_id=execution.application_id,
                application_url="https://example.com/apply",
            )
        except RuntimeError:
            pass

    mock_mark_failed.assert_called_once_with(
        db=db,
        application_id=execution.application_id,
        failure_reason="Browser crashed.",
    )
