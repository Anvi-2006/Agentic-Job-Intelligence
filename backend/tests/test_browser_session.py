from unittest.mock import MagicMock

import pytest

from backend.app.browser.browser_session import BrowserSession


def test_open_url_rejects_non_http_scheme():
    manager = MagicMock()
    session = BrowserSession(manager=manager)

    with pytest.raises(
        ValueError,
        match="Browser URL must use http or https",
    ):
        session.open_url("file:///etc/passwd")

    manager.page.goto.assert_not_called()


def test_open_url_rejects_missing_host():
    manager = MagicMock()
    session = BrowserSession(manager=manager)

    with pytest.raises(
        ValueError,
        match="Browser URL must include a valid host",
    ):
        session.open_url("https:///application")

    manager.page.goto.assert_not_called()


def test_open_url_allows_valid_https_url():
    manager = MagicMock()
    manager.page.url = "https://example.com/jobs/123"
    session = BrowserSession(manager=manager)

    session.open_url("https://example.com/jobs/123")

    manager.page.goto.assert_called_once_with(
        "https://example.com/jobs/123",
        wait_until="domcontentloaded",
    )


def test_open_url_rejects_redirect_to_non_http_url():
    manager = MagicMock()
    manager.page.url = "file:///etc/passwd"

    session = BrowserSession(manager=manager)

    with pytest.raises(
        ValueError,
        match="Browser URL must use http or https",
    ):
        session.open_url("https://example.com/application")

    manager.page.goto.assert_called_once_with(
        "https://example.com/application",
        wait_until="domcontentloaded",
    )
