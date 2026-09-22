from pathlib import Path

from backend.app.browser.browser_manager import BrowserManager
from backend.app.browser.browser_session import BrowserSession


HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>ApplyIQ Browser Test</title>
</head>
<body>
    <h1>Application Form</h1>

    <form>
        <label for="name">Name</label>
        <input id="name" name="name" type="text">

        <label for="email">Email</label>
        <input id="email" name="email" type="email">

        <button id="submit-button" type="button">
            Submit Application
        </button>
    </form>

    <p id="result"></p>

    <script>
        document
            .getElementById("submit-button")
            .addEventListener("click", function () {
                document.getElementById("result").textContent =
                    "Application submitted";
            });
    </script>
</body>
</html>
"""


test_file = Path(__file__).resolve().parent / "browser_test_page.html"
test_file.write_text(HTML, encoding="utf-8")

file_url = test_file.as_uri()


with BrowserManager(headless=True) as manager:
    session = BrowserSession(manager)

    session.open_url(file_url)

    print(f"Page title: {session.get_page_title()}")
    print(f"Page URL: {session.get_current_url()}")

    session.fill_field(
        "#name",
        "Anvi",
    )

    session.fill_field(
        "#email",
        "anvi@example.com",
    )

    name_value = session.find_element(
        "#name"
    ).input_value()

    email_value = session.find_element(
        "#email"
    ).input_value()

    print(f"Name field: {name_value}")
    print(f"Email field: {email_value}")

    session.click(
        "#submit-button"
    )

    result = session.find_element(
        "#result"
    ).text_content()

    print(f"Form result: {result}")

    screenshot_path = (
        Path(__file__).resolve().parent
        / "browser_session_test.png"
    )

    session.screenshot(
        str(screenshot_path)
    )

    print(
        f"Screenshot created: {screenshot_path}"
    )


print("BrowserSession test: PASS")
