from pathlib import Path
from uuid import UUID, uuid4

from backend.app.agents.application_browser_agent import (
    ApplicationBrowserAgent,
)
from backend.app.browser.browser_manager import BrowserManager
from backend.app.browser.browser_session import BrowserSession
from backend.app.core.database import SessionLocal
from backend.app.models.application import Application
from backend.app.models.application_execution import ApplicationExecution
from backend.app.models.application_package import ApplicationPackage
from backend.app.models.execution_event import ExecutionEvent
from backend.app.models.human_input_request import HumanInputRequest
from backend.app.services.application_browser_execution_service import (
    execute_application_browser_step,
)
from backend.app.services.application_execution_service import (
    create_application_execution,
    start_application_execution,
    resume_application_execution,
)
from backend.app.services.human_input_service import (
    answer_human_input_request,
    get_pending_human_input_requests,
)


SOURCE_APPLICATION_ID = UUID(
    "a9234440-f94f-4650-889f-b4d3c463ffd5"
)

TEST_HTML_PATH = (
    Path(__file__).resolve().parent
    / "human_input_browser_test.html"
)


def create_test_html() -> None:
    TEST_HTML_PATH.write_text(
        """
<!DOCTYPE html>
<html>
<head>
    <title>ApplyIQ Human Input Browser Test</title>
</head>
<body>
    <h1>Application Form</h1>

    <form>
        <label>
            Full Name
            <input
                id="full_name"
                name="full_name"
                type="text"
                required
            >
        </label>

        <br><br>

        <label>
            Email
            <input
                id="email"
                name="email"
                type="email"
                required
            >
        </label>

        <br><br>

        <label>
            Resume
            <input
                id="resume"
                name="resume"
                type="file"
                required
            >
        </label>

        <br><br>

        <label>
            Work Preference
            <input
                id="work_preference"
                name="work_preference"
                type="text"
                required
            >
        </label>

        <br><br>

        <label>
            Cover Letter
            <textarea
                id="cover_letter"
                name="cover_letter"
                required
            ></textarea>
        </label>
    </form>
</body>
</html>
        """.strip(),
        encoding="utf-8",
    )


def cleanup_test_data(
    execution_id: UUID | None,
    application_id: UUID | None,
    package_id: UUID | None,
) -> None:
    db = SessionLocal()

    try:
        if execution_id is not None:
            db.query(HumanInputRequest).filter(
                HumanInputRequest.execution_id
                == execution_id
            ).delete(
                synchronize_session=False
            )

            db.query(ExecutionEvent).filter(
                ExecutionEvent.execution_id
                == execution_id
            ).delete(
                synchronize_session=False
            )

            db.query(ApplicationExecution).filter(
                ApplicationExecution.id
                == execution_id
            ).delete(
                synchronize_session=False
            )

        if package_id is not None:
            db.query(ApplicationPackage).filter(
                ApplicationPackage.id
                == package_id
            ).delete(
                synchronize_session=False
            )

        if application_id is not None:
            db.query(Application).filter(
                Application.id
                == application_id
            ).delete(
                synchronize_session=False
            )

        db.commit()

        print(
            "Temporary integration data cleanup: PASS"
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def main() -> None:
    db = SessionLocal()

    temporary_application_id = None
    temporary_package_id = None
    execution_id = None

    try:
        source_application = db.get(
            Application,
            SOURCE_APPLICATION_ID,
        )

        if source_application is None:
            raise ValueError(
                "Source application not found."
            )

        if source_application.status != "approved":
            raise ValueError(
                "Source application is not approved."
            )

        source_package = (
            db.query(ApplicationPackage)
            .filter(
                ApplicationPackage.application_id
                == SOURCE_APPLICATION_ID
            )
            .first()
        )

        if source_package is None:
            raise ValueError(
                "Source application package not found."
            )

        if not source_package.is_valid:
            raise ValueError(
                "Source application package is not valid."
            )

        temporary_application_id = uuid4()

        temporary_application = Application(
            id=temporary_application_id,
            candidate_id=source_application.candidate_id,
            job_id=source_application.job_id,
            fit_score=source_application.fit_score,
            recommendation=source_application.recommendation,
            status="approved",
            reviewer_note=(
                "Temporary application for "
                "human-input browser execution test."
            ),
        )

        db.add(temporary_application)
        db.flush()

        temporary_package_id = uuid4()

        temporary_package = ApplicationPackage(
            id=temporary_package_id,
            application_id=temporary_application_id,
            readiness_score=source_package.readiness_score,
            tailored_summary=source_package.tailored_summary,
            cover_letter=source_package.cover_letter,
            key_strengths=source_package.key_strengths,
            missing_requirements=(
                source_package.missing_requirements
            ),
            application_questions=(
                source_package.application_questions
            ),
            evidence_used=source_package.evidence_used,
            unsupported_claims=(
                source_package.unsupported_claims
            ),
            is_valid=source_package.is_valid,
        )

        db.add(temporary_package)
        db.commit()

        print(
            "Temporary application created:",
            temporary_application_id,
        )

        print(
            "Temporary application package created:",
            temporary_package_id,
        )

    finally:
        db.close()

    create_test_html()

    try:
        execution = create_application_execution(
            db=SessionLocal(),
            application_id=temporary_application_id,
        )

        execution_id = execution["execution_id"]

        print(
            "Execution created:",
            execution_id,
        )

        db = SessionLocal()

        try:
            started = start_application_execution(
                db=db,
                application_id=temporary_application_id,
            )

            print(
                "Initial execution status:",
                execution["status"],
            )

            print(
                "Started execution status:",
                started["status"],
            )

        finally:
            db.close()

        browser_result = (
            execute_application_browser_step(
                application_id=temporary_application_id,
                application_url=(
                    TEST_HTML_PATH.as_uri()
                ),
                headless=True,
            )
        )

        print(
            "First browser execution status:",
            browser_result["status"],
        )

        if browser_result["status"] != "needs_human":
            raise AssertionError(
                "Expected first browser execution "
                "to require human intervention."
            )

        plan = browser_result["plan"]

        blocked_actions = [
            action
            for action in plan["actions"]
            if action["action"] == "needs_human"
        ]

        if len(blocked_actions) != 1:
            raise AssertionError(
                "Expected exactly one blocked human "
                "input action."
            )

        db = SessionLocal()

        try:
            pending_requests = (
                get_pending_human_input_requests(
                    db=db,
                    execution_id=UUID(
                        str(execution_id)
                    ),
                )
            )

            if len(pending_requests) != 1:
                raise AssertionError(
                    "Expected exactly one pending "
                    "human input request."
                )

            human_request = pending_requests[0]

            print(
                "Human input request:",
                human_request["field_name"],
            )

            answer = (
                "I am available to work remotely."
            )

            answered = answer_human_input_request(
                db=db,
                request_id=UUID(
                    human_request["request_id"]
                ),
                answer=answer,
            )

            print(
                "Human input answered:",
                answered["status"],
            )

        finally:
            db.close()

        db = SessionLocal()

        try:
            resumed = resume_application_execution(
                db=db,
                application_id=temporary_application_id,
            )

            print(
                "Resumed execution status:",
                resumed["status"],
            )

        finally:
            db.close()

        second_browser_result = (
            execute_application_browser_step(
                application_id=temporary_application_id,
                application_url=(
                    TEST_HTML_PATH.as_uri()
                ),
                headless=True,
            )
        )

        print(
            "Second browser execution status:",
            second_browser_result["status"],
        )

        if (
            second_browser_result["status"]
            != "executing"
        ):
            raise AssertionError(
                "Expected second browser execution "
                "to continue executing."
            )

        second_plan = second_browser_result[
            "plan"
        ]

        human_input_actions = [
            action
            for action in second_plan["actions"]
            if action.get("field_type")
            == "human_input"
        ]

        if len(human_input_actions) != 1:
            raise AssertionError(
                "Expected exactly one human_input "
                "browser action after answering."
            )

        human_input_action = (
            human_input_actions[0]
        )

        if (
            human_input_action["value"]
            != "I am available to work remotely."
        ):
            raise AssertionError(
                "Human input answer was not passed "
                "into the browser execution plan."
            )

        execution_result = (
            second_browser_result[
                "execution_result"
            ]
        )

        if execution_result["status"] != "executed":
            raise AssertionError(
                "Expected browser execution "
                "to complete."
            )

        print(
            "Human input browser action:",
            human_input_action,
        )

        print(
            "Executed actions:",
            execution_result[
                "executed_actions"
            ],
        )

        db = SessionLocal()

        try:
            events = (
                db.query(ExecutionEvent)
                .filter(
                    ExecutionEvent.execution_id
                    == UUID(str(execution_id))
                )
                .order_by(
                    ExecutionEvent.step.asc(),
                    ExecutionEvent.created_at.asc(),
                )
                .all()
            )

            print(
                "Execution events:"
            )

            for event in events:
                print(
                    event.step,
                    event.event_type,
                    event.action,
                )

            event_types = [
                event.event_type
                for event in events
            ]

            required_events = [
                "EXECUTION_STARTED",
                "BROWSER_HUMAN_INTERVENTION_REQUIRED",
                "EXECUTION_RESUMED",
                "BROWSER_ACTION_EXECUTED",
                "BROWSER_FIELDS_COMPLETED",
            ]

            for required_event in required_events:
                if required_event not in event_types:
                    raise AssertionError(
                        f"Missing execution event: "
                        f"{required_event}"
                    )

        finally:
            db.close()

        print(
            "HUMAN INPUT BROWSER EXECUTION TEST: PASS"
        )

    finally:
        cleanup_test_data(
            execution_id=(
                UUID(str(execution_id))
                if execution_id is not None
                else None
            ),
            application_id=temporary_application_id,
            package_id=temporary_package_id,
        )

        if TEST_HTML_PATH.exists():
            TEST_HTML_PATH.unlink()

            print(
                "Temporary HTML cleanup: PASS"
            )


if __name__ == "__main__":
    main()