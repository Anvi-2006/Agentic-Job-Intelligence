from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    sync_playwright,
)


class BrowserManager:
    def __init__(
        self,
        headless: bool = True,
    ) -> None:
        self.headless = headless
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    def start(self) -> Page:
        if self._page is not None:
            return self._page

        self._playwright = sync_playwright().start()

        self._browser = self._playwright.chromium.launch(
            headless=self.headless,
        )

        self._context = self._browser.new_context()

        self._page = self._context.new_page()

        return self._page

    def close(self) -> None:
        if self._context is not None:
            self._context.close()
            self._context = None

        if self._browser is not None:
            self._browser.close()
            self._browser = None

        if self._playwright is not None:
            self._playwright.stop()
            self._playwright = None

        self._page = None

    @property
    def page(self) -> Page:
        if self._page is None:
            raise RuntimeError(
                "Browser has not been started."
            )

        return self._page

    def __enter__(self) -> "BrowserManager":
        self.start()
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        self.close()
