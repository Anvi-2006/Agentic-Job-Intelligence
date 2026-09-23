from pathlib import Path
from uuid import UUID

from backend.app.core.database import SessionLocal
from backend.app.models.application import Application
from backend.app.models.application_execution import ApplicationExecution
from backend.app.models.application_package import ApplicationPackage
from backend.app.models.execution_event import ExecutionEvent

from backend.app.services.application_browser_execution_service import (
    execute_application_browser_step,
)
from backend.app.services.application_execution_service import (
    create_application_execution,
    start_application_execution,
)


SOURCE_APPLICATION_ID = UUID(
    "69872582-adea-400b-be7f-e054780165e5"
)


def create_local_application_page(
    path: Path,
) -> None:
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>ApplyIQ Integration Test</title>
</head>
<body>
    <h1>Python Backend Intern Application</h1>

    <form id="application-form">
        <label for="full-name">Full Name</label>
        <input
            id="full-name"
            name="full_name"
            type="text"
            required
        >

        <label for="email">Email</label>
        <input
            id="email"
            name="email"
            type="email"
            required
        >

        <label for="resume">Resume</label>
        <input
            id="resume"
            name="resume"
            type="file"
            required
        >

        <label for="cover-letter">Cover Letter</label>
        <textarea
            id="cover-letter"
            name="cover_letter"
        ></textarea>

        <button
            id="submit-button"
            type="button"
        >
            Submit Application
        </button>
    </form>
</body>
</html>
"""

    path.write_text(
        html,
        encoding="utf-8",
    )


def main() -> None:
    db = SessionLocal()

    page_path = (
        Path.cwd()
        / "backend"
        / "app"
        / "scripts"
        / "browser_execution_integration_test.html"
    )

    temporary_application_id = None
    temporary_execution_id = None
    temporary_package_id = None

    try:
        source_application = db.get(
            Application,
            SOURCE_APPLICATION_ID,
        )

        if source_application is None:
            raise RuntimeError(
                "Source application was not found."
            )

        if (
            source_application.status.lower()
            != "approved"
        ):
            raise RuntimeError(
                "Source application is not approved."
            )

        source_package = (
            db.query(ApplicationPackage)
            .filter(
                ApplicationPackage.application_id
                == source_application.id,
            )
            .first()
        )

        if source_package is None:
            raise RuntimeError(
                "Source application package was not found."
            )

        if not source_package.is_valid:
            raise RuntimeError(
                "Source application package is not valid."
            )

        print(
            f"Source application: "
            f"{source_application.id}"
        )

        print(
            f"Source package: "
            f"{source_package.id}"
        )

        print(
            f"Source package valid: "
            f"{source_package.is_valid}"
        )

        temporary_application = Application(
            candidate_id=(
                source_application.candidate_id
            ),
            job_id=source_application.job_id,
            fit_score=source_application.fit_score,
            recommendation=(
                source_application.recommendation
            ),
            status="approved",
            reviewer_note=(
                "Temporary browser integration test."
            ),
        )

        db.add(temporary_application)
        db.flush()

        temporary_application_id = (
            temporary_application.id
        )

        temporary_package = ApplicationPackage(
            application_id=(
                temporary_application.id
            ),
            readiness_score=(
                source_package.readiness_score
            ),
            tailored_summary=(
                source_package.tailored_summary
            ),
            cover_letter=(
                source_package.cover_letter
            ),
            key_strengths=(
                source_package.key_strengths
            ),
            missing_requirements=(
                source_package.missing_requirements
            ),
            application_questions=(
                source_package.application_questions
            ),
            evidence_used=(
                source_package.evidence_used
            ),
            unsupported_claims=(
                source_package.unsupported_claims
            ),
            is_valid=source_package.is_valid,
        )

        db.add(temporary_package)
        db.commit()
        db.refresh(temporary_application)
        db.refresh(temporary_package)

        temporary_package_id = (
            temporary_package.id
        )

        print(
            f"Temporary application: "
            f"{temporary_application.id}"
        )

        print(
            f"Temporary package: "
            f"{temporary_package.id}"
        )

        execution_result = (
            create_application_execution(
                db=db,
                application_id=(
                    temporary_application.id
                ),
            )
        )

        temporary_execution_id = UUID(
            execution_result[
                "execution_id"
            ]
        )

        print(
            f"Initial execution status: "
            f"{execution_result['status']}"
        )

        start_result = (
            start_application_execution(
                db=db,
                application_id=(
                    temporary_application.id
                ),
            )
        )

        print(
            f"Started execution status: "
            f"{start_result['status']}"
        )

        create_local_application_page(
            page_path
        )

        application_url = (
            page_path.resolve().as_uri()
        )

        print(
            f"Application URL: "
            f"{application_url}"
        )

        result = execute_application_browser_step(
            application_id=(
                temporary_application.id
            ),
            application_url=application_url,
            headless=True,
        )

        print(
            f"Browser execution status: "
            f"{result['status']}"
        )

        print(
            f"Execution step: "
            f"{result['execution']['current_step']}"
        )

        print(
            f"Execution action: "
            f"{result['execution']['current_action']}"
        )

        assert result["status"] == "executing"

        assert (
            result["execution"][
                "current_action"
            ]
            == "browser_fields_completed"
        )

        event_rows = (
            db.query(ExecutionEvent)
            .filter(
                ExecutionEvent.execution_id
                == temporary_execution_id,
            )
            .order_by(
                ExecutionEvent.step.asc(),
                ExecutionEvent.created_at.asc(),
                ExecutionEvent.id.asc(),
            )
            .all()
        )

        event_types = [
            event.event_type
            for event in event_rows
        ]

        print("Execution events:")

        for event in event_rows:
            print(
                {
                    "event_type": event.event_type,
                    "step": event.step,
                    "action": event.action,
                    "success": event.success,
                }
            )

        assert (
            "EXECUTION_STARTED"
            in event_types
        )

        assert (
            "BROWSER_ACTION_EXECUTED"
            in event_types
        )

        assert (
            "BROWSER_FIELDS_COMPLETED"
            in event_types
        )

        print(
            "Browser execution integration test: PASS"
        )

    finally:
        if page_path.exists():
            page_path.unlink()

        cleanup_db = SessionLocal()

        try:
            if temporary_execution_id is not None:
                cleanup_db.query(
                    ExecutionEvent
                ).filter(
                    ExecutionEvent.execution_id
                    == temporary_execution_id,
                ).delete(
                    synchronize_session=False
                )

                cleanup_db.query(
                    ApplicationExecution
                ).filter(
                    ApplicationExecution.id
                    == temporary_execution_id,
                ).delete(
                    synchronize_session=False
                )

            if temporary_package_id is not None:
                cleanup_db.query(
                    ApplicationPackage
                ).filter(
                    ApplicationPackage.id
                    == temporary_package_id,
                ).delete(
                    synchronize_session=False
                )

            if temporary_application_id is not None:
                cleanup_db.query(
                    Application
                ).filter(
                    Application.id
                    == temporary_application_id,
                ).delete(
                    synchronize_session=False
                )

            cleanup_db.commit()

            print(
                "Temporary integration data cleanup: PASS"
            )

        finally:
            cleanup_db.close()

        db.close()


if __name__ == "__main__":
    main()