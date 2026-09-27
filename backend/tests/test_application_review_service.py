import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

from types import SimpleNamespace
from uuid import UUID
from unittest.mock import MagicMock

import pytest

from backend.app.services.application_review_service import (
    review_application,
)


CANDIDATE_ID = UUID(
    "332b3f24-eefc-4d05-99d5-56798d24a50c"
)

APPLICATION_ID = UUID(
    "a9234440-f94f-4650-889f-b4d3c463ffd5"
)

JOB_ID = UUID(
    "5720e13e-bbc2-4ee4-8cbd-25497b83eb2e"
)


def test_review_application_rejects_invalid_decision():
    db = MagicMock()

    with pytest.raises(
        ValueError,
        match="Invalid decision",
    ):
        review_application(
            db=db,
            candidate_id=CANDIDATE_ID,
            job_id=JOB_ID,
            decision="INVALID",
        )


def test_review_application_approves_valid_application():
    db = MagicMock()

    candidate = SimpleNamespace(
        id=CANDIDATE_ID,
    )

    job = SimpleNamespace(
        id=JOB_ID,
        company="Demo Company",
        title="Software Engineer",
    )

    application = SimpleNamespace(
        id=APPLICATION_ID,
        candidate_id=CANDIDATE_ID,
        job_id=JOB_ID,
        fit_score=90.0,
        recommendation="APPLY",
        status="pending_review",
        reviewer_note=None,
    )

    application_package = SimpleNamespace(
        application_id=APPLICATION_ID,
        is_valid=True,
    )

    db.get.side_effect = [
        candidate,
        job,
    ]

    application_query = MagicMock()
    application_query.filter.return_value.first.return_value = application

    package_query = MagicMock()
    package_query.filter.return_value.first.return_value = application_package

    db.query.side_effect = [
        application_query,
        package_query,
    ]

    db.refresh.side_effect = lambda obj: None

    result = review_application(
        db=db,
        candidate_id=CANDIDATE_ID,
        job_id=JOB_ID,
        decision="APPROVED",
        reviewer_note="Approved for submission.",
    )

    assert result["status"] == "approved"
    assert result["reviewer_note"] == "Approved for submission."
    assert result["application_id"] == str(
        APPLICATION_ID
    )

    assert application.status == "approved"
    assert application.reviewer_note == "Approved for submission."

    db.commit.assert_called_once()