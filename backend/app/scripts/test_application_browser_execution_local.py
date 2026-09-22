from pathlib import Path
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


APPLICATION_ID = UUID(
    "a9234440-f94f-4650-889f-b4d3c463ffd5"
)


HTML_FILE = Path(
    "backend/app/scripts/"
    "browser_execution_test_page.html"
)


HTML_CONTENT = """
<!DOCTYPE html>
<html>
<head>
    <title>ApplyIQ Local Application Test</title>
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


def main() -> None:
    db = SessionLocal()
    manager = BrowserManager(
        headless=True,
    )
    manager.start()

    try:
        application_data = build_application_data(
            db=db,
            application_id=APPLICATION_ID,
        )

        resume_path = application_data[
            "resume"
        ]["file_path"]

        if not resume_path:
            raise AssertionError(
                "Resume path is missing."
            )

        absolute_resume_path = (
            Path(resume_path)
            .resolve()
        )

        if not absolute_resume_path.exists():
            raise AssertionError(
                f"Resume file does not exist: "
                f"{absolute_resume_path}"
            )

        HTML_FILE.write_text(
            HTML_CONTENT,
            encoding="utf-8",
        )

        session = BrowserSession(manager)
        agent = ApplicationBrowserAgent(
            session
        )

        page_data = agent.open_application_page(
            HTML_FILE.resolve().as_uri()
        )

        print(
            "Application form detected:",
            agent.detect_application_form(),
        )

        print(
            "Detected fields:",
            page_data["field_count"],
        )

        plan = agent.build_execution_plan(
            page_data=page_data,
            application_data=application_data,
        )

        print("Execution plan:")

        for action in plan["actions"]:
            print(action)

        assert (
            plan["human_intervention_required"]
            is False
        )

        result = agent.execute_plan(
            plan
        )

        print("Execution result:")
        print(result)

        assert result["status"] == "executed"

        page = session.page

        full_name = page.locator(
            "#full-name"
        ).input_value()

        email = page.locator(
            "#email"
        ).input_value()

        cover_letter = page.locator(
            "#cover-letter"
        ).input_value()

        uploaded_files = page.locator(
            "#resume"
        ).evaluate(
            """
            (element) =>
                Array.from(element.files)
                    .map(file => file.name)
            """
        )

        print("Full name:", full_name)
        print("Email:", email)
        print(
            "Cover letter:",
            cover_letter,
        )
        print(
            "Uploaded files:",
            uploaded_files,
        )

        assert full_name == (
            application_data[
                "candidate"
            ]["full_name"]
        )

        assert email == (
            application_data[
                "candidate"
            ]["email"]
        )

        assert cover_letter == (
            application_data[
                "application_package"
            ]["cover_letter"]
        )

        assert (
    	    absolute_resume_path.name
            in uploaded_files
        )

        print(
            "Local browser execution test: PASS"
        )

    finally:
        manager.close()
        db.close()

        if HTML_FILE.exists():
            HTML_FILE.unlink()


if __name__ == "__main__":
    main()