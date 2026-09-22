from uuid import UUID

from backend.app.agents.application_browser_agent import (
    ApplicationBrowserAgent,
)
from backend.app.browser.browser_manager import BrowserManager
from backend.app.browser.browser_session import BrowserSession
from backend.app.core.database import SessionLocal
from backend.app.services.application_data_service import (
    build_application_data,
)
from backend.app.services.application_execution_service import (
    EXECUTION_STATUS_EXECUTING,
    EXECUTION_STATUS_NEEDS_HUMAN,
    _get_execution,
)
from backend.app.services.execution_event_service import (
    record_execution_event,
)
from backend.app.services.human_input_service import (
    create_human_input_request,
    get_answered_human_input_requests,
)


def execute_application_browser_step(
    application_id: UUID,
    application_url: str,
    headless: bool = True,
) -> dict:
    """
    Execute the approved application's browser-safe actions.

    This service connects the execution state machine to the
    browser agent without allowing the browser agent to own
    execution state.

    Submission is intentionally NOT performed here.
    """

    db = SessionLocal()

    try:
        execution = _get_execution(
            db=db,
            application_id=application_id,
        )

        if execution.status != EXECUTION_STATUS_EXECUTING:
            raise ValueError(
                "Browser execution can only run while "
                "the application execution is in progress."
            )

        application_data = build_application_data(
            db=db,
            application_id=application_id,
        )

        answered_human_inputs = (
            get_answered_human_input_requests(
                db=db,
                execution_id=execution.id,
            )
        )

        application_data["human_inputs"] = {
            item["field_name"]: item["answer"]
            for item in answered_human_inputs
        }

        with BrowserManager(
            headless=headless,
        ) as manager:
            session = BrowserSession(
                manager=manager,
            )

            agent = ApplicationBrowserAgent(
                session=session,
            )

            page_data = agent.open_application_page(
                application_url,
            )

            form_detected = (
                agent.detect_application_form()
            )

            if not form_detected:
                raise ValueError(
                    "No application form was detected "
                    "on the application page."
                )

            plan = agent.build_execution_plan(
                page_data=page_data,
                application_data=application_data,
            )

            if plan.get(
                "human_intervention_required",
                False,
            ):
                execution.status = (
                    EXECUTION_STATUS_NEEDS_HUMAN
                )

                execution.current_action = (
                    "browser_human_intervention"
                )

                blocked_actions = [
                    action
                    for action in plan.get(
                        "actions",
                        [],
                    )
                    if action.get("action")
                    == "needs_human"
                ]

                for blocked_action in blocked_actions:
                    create_human_input_request(
                        db=db,
                        execution_id=execution.id,
                        field_name=blocked_action[
                            "selector"
                        ],
                        question=(
                            "Please provide the information "
                            "required for the application field "
                            f"{blocked_action['selector']}."
                        ),
                    )

                record_execution_event(
                    db=db,
                    execution_id=execution.id,
                    event_type=(
                        "BROWSER_HUMAN_INTERVENTION_REQUIRED"
                    ),
                    step=execution.current_step + 1,
                    action=(
                        "browser_human_intervention"
                    ),
                    details=(
                        f"Browser execution paused. "
                        f"{len(blocked_actions)} "
                        f"required field(s) need "
                        f"human intervention."
                    ),
                    success=True,
                    commit=False,
                )

                db.commit()
                db.refresh(execution)

                return {
                    "status": (
                        EXECUTION_STATUS_NEEDS_HUMAN
                    ),
                    "application_id": str(
                        application_id
                    ),
                    "execution_id": str(
                        execution.id
                    ),
                    "form_detected": form_detected,
                    "page": page_data,
                    "plan": plan,
                    "execution": {
                        "current_step": (
                            execution.current_step
                        ),
                        "current_action": (
                            execution.current_action
                        ),
                    },
                }

            result = agent.execute_plan(
                plan=plan,
            )

            if result.get("status") != "executed":
                raise ValueError(
                    result.get(
                        "message",
                        "Browser execution failed.",
                    )
                )

            executed_actions = result.get(
                "executed_actions",
                [],
            )

            for index, action in enumerate(
                executed_actions,
                start=1,
            ):
                record_execution_event(
                    db=db,
                    execution_id=execution.id,
                    event_type=(
                        "BROWSER_ACTION_EXECUTED"
                    ),
                    step=execution.current_step + index,
                    action=action["action"],
                    details=(
                        f"Browser action executed "
                        f"successfully for selector "
                        f"{action['selector']}."
                    ),
                    success=action["success"],
                    commit=False,
                )

            execution.current_step = (
                execution.current_step
                + len(executed_actions)
            )

            execution.current_action = (
                "browser_fields_completed"
            )

            record_execution_event(
                db=db,
                execution_id=execution.id,
                event_type=(
                    "BROWSER_FIELDS_COMPLETED"
                ),
                step=execution.current_step + 1,
                action=(
                    "browser_fields_completed"
                ),
                details=(
                    f"{len(executed_actions)} "
                    f"browser action(s) completed. "
                    f"Application submission was not "
                    f"performed."
                ),
                success=True,
                commit=False,
            )

            db.commit()
            db.refresh(execution)

            return {
                "status": execution.status,
                "application_id": str(
                    application_id
                ),
                "execution_id": str(
                    execution.id
                ),
                "form_detected": form_detected,
                "page": page_data,
                "plan": plan,
                "execution_result": result,
                "execution": {
                    "current_step": (
                        execution.current_step
                    ),
                    "current_action": (
                        execution.current_action
                    ),
                },
            }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()