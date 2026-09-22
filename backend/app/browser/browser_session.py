from playwright.sync_api import Page

from backend.app.browser.browser_manager import BrowserManager


class BrowserSession:
    def __init__(
        self,
        manager: BrowserManager,
    ) -> None:
        self.manager = manager

    @property
    def page(self) -> Page:
        return self.manager.page

    def open_url(self, url: str) -> None:
        if not url.strip():
            raise ValueError("Browser URL cannot be empty.")

        self.page.goto(
            url,
            wait_until="domcontentloaded",
        )

    def get_page_title(self) -> str:
        return self.page.title()

    def get_current_url(self) -> str:
        return self.page.url

    def find_element(self, selector: str):
        if not selector.strip():
            raise ValueError(
                "Browser selector cannot be empty."
            )

        return self.page.locator(selector)

    def fill_field(
        self,
        selector: str,
        value: str,
    ) -> None:
        if not selector.strip():
            raise ValueError(
                "Browser selector cannot be empty."
            )

        self.page.locator(selector).fill(value)

    def click(
        self,
        selector: str,
    ) -> None:
        if not selector.strip():
            raise ValueError(
                "Browser selector cannot be empty."
            )

        self.page.locator(selector).click()

    def wait_for_navigation(self) -> None:
        self.page.wait_for_load_state(
            "domcontentloaded",
        )

    def screenshot(
        self,
        path: str,
    ) -> None:
        if not path.strip():
            raise ValueError(
                "Screenshot path cannot be empty."
            )

        self.page.screenshot(
            path=path,
            full_page=True,
        )
