from backend.app.browser.browser_manager import BrowserManager


with BrowserManager(headless=True) as manager:
    page = manager.page
    page.goto("https://example.com")

    print(f"Page title: {page.title()}")
    print(f"Page URL: {page.url}")

print("Browser lifecycle: PASS")
