from pathlib import Path

from backend.app.agents.application_browser_agent import (
    ApplicationBrowserAgent,
)
from backend.app.browser.browser_manager import BrowserManager
from backend.app.browser.browser_session import BrowserSession


HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>ApplyIQ Application Test</title>
</head>
<body>

    <h1>Apply for Python Backend Intern</h1>

    <form id="application-form">

        <label for="full-name">Full Name</label>
        <input
            id="full-name"
            name="full_name"
            type="text"
            placeholder="Enter your full name"
            required
        >

        <label for="email">Email</label>
        <input
            id="email"
            name="email"
            type="email"
            placeholder="Enter your email"
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
            placeholder="Enter your cover letter"
        ></textarea>

        <button type="submit">
            Apply
        </button>

    </form>

</body>
</html>
"""


test_file = (
    Path(__file__).resolve().parent
    / "browser_agent_test_page.html"
)

test_file.write_text(
    HTML,
    encoding="utf-8",
)

file_url = test_file.as_uri()


with BrowserManager(headless=True) as manager:
    session = BrowserSession(manager)

    agent = ApplicationBrowserAgent(
        session=session,
    )

    inspection = agent.open_application_page(
        file_url,
    )

    print(
        f"Page title: {inspection['title']}"
    )

    print(
        f"Page URL: {inspection['url']}"
    )

    print(
        f"Form count: {inspection['form_count']}"
    )

    print(
        f"Field count: {inspection['field_count']}"
    )

    print(
        f"Application form detected: "
        f"{agent.detect_application_form()}"
    )

    for field in inspection["fields"]:
        print(
            "Field:",
            field,
        )


test_file.unlink()

print("ApplicationBrowserAgent inspection test: PASS")
