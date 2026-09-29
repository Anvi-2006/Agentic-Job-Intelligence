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
def test_browser_execution_pauses_for_human_when_no_form_is_detected():
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

    mock_manager = MagicMock()
    mock_session = MagicMock()
    mock_agent = MagicMock()

    mock_agent.open_application_page.return_value = {
        "title": "Example Careers",
        "url": "https://example.com/apply",
        "fields": [],
    }
    mock_agent.detect_application_form.return_value = False

    with patch(
        "backend.app.services.application_browser_execution_service.SessionLocal",
        return_value=db,
    ), patch(
        "backend.app.services.application_browser_execution_service.build_application_data",
        return_value={},
    ), patch(
        "backend.app.services.application_browser_execution_service.get_answered_human_input_requests",
        return_value=[],
    ), patch(
        "backend.app.services.application_browser_execution_service.BrowserManager",
        return_value=mock_manager,
    ), patch(
        "backend.app.services.application_browser_execution_service.BrowserSession",
        return_value=mock_session,
    ), patch(
        "backend.app.services.application_browser_execution_service.ApplicationBrowserAgent",
        return_value=mock_agent,
    ), patch(
        "backend.app.services.application_browser_execution_service.create_human_input_request",
    ) as mock_create_request, patch(
        "backend.app.services.application_browser_execution_service.record_execution_event",
    ) as mock_record_event:
        result = execute_application_browser_step(
            application_id=execution.application_id,
            application_url="https://example.com/apply",
        )

    assert result["status"] == "needs_human"
    assert result["application_id"] == str(execution.application_id)
    assert result["form_detected"] is False
    assert result["execution"]["current_step"] == 2
    assert result["execution"]["current_action"] == "browser_human_intervention"

    assert execution.status == "needs_human"
    assert execution.current_action == "browser_human_intervention"

    mock_create_request.assert_called_once()
    mock_record_event.assert_called_once()
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(execution)
def test_browser_execution_pauses_for_human_when_required_field_needs_input():
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

    mock_manager = MagicMock()
    mock_session = MagicMock()
    mock_agent = MagicMock()

    page_data = {
        "title": "Example Careers",
        "url": "https://example.com/apply",
        "fields": [
            {
                "tag": "input",
                "type": "text",
                "name": "portfolio",
                "placeholder": "Portfolio URL",
                "required": True,
                "selector": 'input[name="portfolio"]',
            }
        ],
    }

    plan = {
        "human_intervention_required": True,
        "actions": [
            {
                "action": "needs_human",
                "selector": 'input[name="portfolio"]',
            }
        ],
    }

    mock_agent.open_application_page.return_value = page_data
    mock_agent.detect_application_form.return_value = True
    mock_agent.build_execution_plan.return_value = plan

    with patch(
        "backend.app.services.application_browser_execution_service.SessionLocal",
        return_value=db,
    ), patch(
        "backend.app.services.application_browser_execution_service.build_application_data",
        return_value={},
    ), patch(
        "backend.app.services.application_browser_execution_service.get_answered_human_input_requests",
        return_value=[],
    ), patch(
        "backend.app.services.application_browser_execution_service.BrowserManager",
        return_value=mock_manager,
    ), patch(
        "backend.app.services.application_browser_execution_service.BrowserSession",
        return_value=mock_session,
    ), patch(
        "backend.app.services.application_browser_execution_service.ApplicationBrowserAgent",
        return_value=mock_agent,
    ), patch(
        "backend.app.services.application_browser_execution_service.create_human_input_request",
    ) as mock_create_request, patch(
        "backend.app.services.application_browser_execution_service.record_execution_event",
    ) as mock_record_event:
        result = execute_application_browser_step(
            application_id=execution.application_id,
            application_url="https://example.com/apply",
        )

    assert result["status"] == "needs_human"
    assert result["application_id"] == str(execution.application_id)
    assert result["form_detected"] is True
    assert result["plan"] == plan
    assert result["execution"]["current_step"] == 2
    assert result["execution"]["current_action"] == "browser_human_intervention"

    assert execution.status == "needs_human"
    assert execution.current_action == "browser_human_intervention"

    mock_create_request.assert_called_once_with(
        db=db,
        execution_id=execution.id,
        field_name='input[name="portfolio"]',
        question=(
            "Please provide the information required for the "
            'application field input[name="portfolio"].'
        ),
    )

    mock_record_event.assert_called_once()
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(execution)
def test_browser_execution_completes_fields_without_submitting():
    db = MagicMock()

    execution = SimpleNamespace(
        id=uuid4(),
        application_id=uuid4(),
        status="executing",
        current_step=2,
        current_action="browser_started",
        submission_approved=False,
        failure_reason=None,
    )

    db.query.return_value.filter.return_value.first.return_value = execution

    mock_manager = MagicMock()
    mock_session = MagicMock()
    mock_agent = MagicMock()

    page_data = {
        "title": "Example Careers",
        "url": "https://example.com/apply",
        "fields": [],
    }

    plan = {
        "human_intervention_required": False,
        "actions": [
            {
                "action": "fill",
                "selector": 'input[name="email"]',
                "value": "candidate@example.com",
            }
        ],
    }

    execution_result = {
        "status": "executed",
        "executed_actions": [
            {
                "action": "fill",
                "selector": 'input[name="email"]',
                "success": True,
            }
        ],
    }

    mock_agent.open_application_page.return_value = page_data
    mock_agent.detect_application_form.return_value = True
    mock_agent.build_execution_plan.return_value = plan
    mock_agent.execute_plan.return_value = execution_result

    with patch(
        "backend.app.services.application_browser_execution_service.SessionLocal",
        return_value=db,
    ), patch(
        "backend.app.services.application_browser_execution_service.build_application_data",
        return_value={},
    ), patch(
        "backend.app.services.application_browser_execution_service.get_answered_human_input_requests",
        return_value=[],
    ), patch(
        "backend.app.services.application_browser_execution_service.BrowserManager",
        return_value=mock_manager,
    ), patch(
        "backend.app.services.application_browser_execution_service.BrowserSession",
        return_value=mock_session,
    ), patch(
        "backend.app.services.application_browser_execution_service.ApplicationBrowserAgent",
        return_value=mock_agent,
    ), patch(
        "backend.app.services.application_browser_execution_service.record_execution_event",
    ) as mock_record_event:
        result = execute_application_browser_step(
            application_id=execution.application_id,
            application_url="https://example.com/apply",
        )

    assert result["status"] == "executing"
    assert result["application_id"] == str(execution.application_id)
    assert result["form_detected"] is True
    assert result["plan"] == plan
    assert result["execution_result"] == execution_result

    assert execution.current_step == 3
    assert execution.current_action == "browser_fields_completed"
    assert execution.submission_approved is False

    assert mock_record_event.call_count == 2
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(execution)

    mock_agent.execute_plan.assert_called_once_with(plan=plan)


def test_browser_execution_pauses_for_human_when_agent_returns_needs_human():
    db = MagicMock()

    execution = SimpleNamespace(
        id=uuid4(),
        application_id=uuid4(),
        status="executing",
        current_step=2,
        current_action="browser_started",
        submission_approved=False,
        failure_reason=None,
    )

    db.query.return_value.filter.return_value.first.return_value = execution

    mock_manager = MagicMock()
    mock_session = MagicMock()
    mock_agent = MagicMock()

    page_data = {
        "title": "Example Careers",
        "url": "https://example.com/apply",
        "fields": [],
    }

    plan = {
        "human_intervention_required": False,
        "actions": [
            {
                "action": "fill",
                "selector": 'input[name="email"]',
                "value": "candidate@example.com",
            }
        ],
    }

    execution_result = {
        "status": "needs_human",
        "message": "Human intervention is required.",
        "executed_actions": [],
    }

    mock_agent.open_application_page.return_value = page_data
    mock_agent.detect_application_form.return_value = True
    mock_agent.build_execution_plan.return_value = plan
    mock_agent.execute_plan.return_value = execution_result

    with patch(
        "backend.app.services.application_browser_execution_service.SessionLocal",
        return_value=db,
    ), patch(
        "backend.app.services.application_browser_execution_service.build_application_data",
        return_value={},
    ), patch(
        "backend.app.services.application_browser_execution_service.get_answered_human_input_requests",
        return_value=[],
    ), patch(
        "backend.app.services.application_browser_execution_service.BrowserManager",
        return_value=mock_manager,
    ), patch(
        "backend.app.services.application_browser_execution_service.BrowserSession",
        return_value=mock_session,
    ), patch(
        "backend.app.services.application_browser_execution_service.ApplicationBrowserAgent",
        return_value=mock_agent,
    ), patch(
        "backend.app.services.application_browser_execution_service.create_human_input_request",
    ) as mock_create_request, patch(
        "backend.app.services.application_browser_execution_service.record_execution_event",
    ) as mock_record_event:
        
        result = execute_application_browser_step(
            application_id=execution.application_id,
            application_url="https://example.com/apply",
        )

    assert result["status"] == "needs_human"

    mock_create_request.assert_not_called()
    mock_record_event.assert_called_once()
    
    
