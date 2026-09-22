from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models.application import Application
from backend.app.models.application_execution import ApplicationExecution
from backend.app.models.application_package import ApplicationPackage
from backend.app.models.human_input_request import (
    HUMAN_INPUT_STATUS_PENDING,
    HumanInputRequest,
)
from backend.app.services.application_execution_service import (
    EXECUTION_STATUS_EXECUTING,
    _get_execution,
)


def validate_application_submission(
    db: Session,
    application_id: UUID,
) -> dict:
    """
    Validate whether an application is currently allowed
    to proceed to the final submission step.

    This function performs validation only.
    It does not interact with the browser and does not
    submit the application.
    """

    application = db.get(
        Application,
        application_id,
    )

    if application is None:
        raise ValueError(
            "Application not found."
        )

    if application.status.lower() != "approved":
        raise ValueError(
            "Application must be approved before submission."
        )

    package = (
        db.query(ApplicationPackage)
        .filter(
            ApplicationPackage.application_id
            == application.id,
        )
        .first()
    )

    if package is None:
        raise ValueError(
            "Application package not found."
        )

    if not package.is_valid:
        raise ValueError(
            "Application package is not valid for submission."
        )

    execution = _get_execution(
        db=db,
        application_id=application_id,
    )

    if execution.status != EXECUTION_STATUS_EXECUTING:
        raise ValueError(
            "Application execution must be in progress "
            "before submission."
        )

    pending_human_inputs = (
        db.query(HumanInputRequest)
        .filter(
            HumanInputRequest.execution_id == execution.id,
            HumanInputRequest.status
            == HUMAN_INPUT_STATUS_PENDING,
        )
        .all()
    )

    if pending_human_inputs:
        raise ValueError(
            "Submission cannot proceed while required "
            "human input is still pending."
        )

    if not execution.submission_approved:
        raise ValueError(
            "Explicit human submission approval is required "
            "before the application can be submitted."
        )

    return {
        "application_id": str(application.id),
        "execution_id": str(execution.id),
        "approved": True,
        "package_valid": True,
        "execution_ready": True,
        "human_inputs_complete": True,
        "submission_approval": True,
        "submission_allowed": True,
    }