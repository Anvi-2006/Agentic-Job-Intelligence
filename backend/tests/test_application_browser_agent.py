from pathlib import Path
from unittest.mock import MagicMock

import pytest

from backend.app.agents.application_browser_agent import (
    ApplicationBrowserAgent,
)


def test_execute_upload_rejects_file_outside_resume_directory(
    tmp_path,
):
    session = MagicMock()
    agent = ApplicationBrowserAgent(session=session)

    outside_file = tmp_path / "malicious.pdf"
    outside_file.write_bytes(b"test")

    with pytest.raises(
        ValueError,
        match="existing resume inside uploads/resumes",
    ):
        agent.execute_upload(
            selector="#resume",
            file_path=str(outside_file),
        )

    session.page.locator.assert_not_called()


def test_execute_upload_rejects_missing_resume_file():
    session = MagicMock()
    agent = ApplicationBrowserAgent(session=session)

    missing_file = (
        Path("uploads/resumes")
        / "missing-resume.pdf"
    )

    with pytest.raises(
        ValueError,
        match="existing resume inside uploads/resumes",
    ):
        agent.execute_upload(
            selector="#resume",
            file_path=str(missing_file),
        )

    session.page.locator.assert_not_called()