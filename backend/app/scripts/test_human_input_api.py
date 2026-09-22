from uuid import UUID

from fastapi.testclient import TestClient

from backend.app.core.database import SessionLocal
from backend.app.main import app
from backend.app.models.application import Application
from backend.app.models.application_execution import ApplicationExecution
from backend.app.models.application_package import ApplicationPackage
from backend.app.services.application_execution_service import (
    create_application_execution,
)
from backend.app.services.human_input_service import (
    create_human_input_request,
)
from backend.app.models.human_input_request import (
    HumanInputRequest,
)


client = TestClient(app)


def main():
    db = SessionLocal()

    application = None
    package = None
    execution = None
    human_request = None

    try:
        # Find an approved application/package that can be used
        # as the source for this integration test.
        application = (
            db.query(Application)
            .filter(
                Application.status == "approved",
            )
            .first()
        )

        if application is None:
            raise RuntimeError(
                "No approved application exists for the test."
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
            raise RuntimeError(
                "No application package exists for the test."
            )

        execution = create_application_execution(
            db=db,
            application_id=application.id,
        )

        print(
            f"Temporary execution: {execution['execution_id']}"
        )

        execution_id = UUID(
            execution["execution_id"]
        )

        # Create the human input request directly through
        # the service first.
        human_request = create_human_input_request(
            db=db,
            execution_id=execution_id,
            field_name="why_should_we_hire_you",
            question=(
                "Why should we hire you?"
            ),
        )

        request_id = UUID(
            human_request["request_id"]
        )

        print(
            "Human input request creation: PASS"
        )

        # Retrieve pending human input through the API.
        response = client.get(
            f"/api/executions/{execution_id}/human-input"
        )

        print(
            f"Get human input: {response.status_code}"
        )

        assert response.status_code == 200

        pending_requests = response.json()

        assert len(pending_requests) == 1

        assert (
            pending_requests[0]["request_id"]
            == str(request_id)
        )

        assert (
            pending_requests[0]["field_name"]
            == "why_should_we_hire_you"
        )

        assert (
            pending_requests[0]["status"]
            == "pending"
        )

        print(
            "Get pending human input API: PASS"
        )

        # Submit the human's answer.
        response = client.post(
            f"/api/executions/human-input/"
            f"{request_id}/answer",
            json={
                "answer": (
                    "I have experience building "
                    "Python and FastAPI applications "
                    "and I am interested in backend "
                    "engineering."
                )
            },
        )

        print(
            f"Answer human input: {response.status_code}"
        )

        assert response.status_code == 200

        answered_request = response.json()

        assert (
            answered_request["request_id"]
            == str(request_id)
        )

        assert (
            answered_request["status"]
            == "answered"
        )

        assert answered_request["answer"] == (
            "I have experience building "
            "Python and FastAPI applications "
            "and I am interested in backend "
            "engineering."
        )

        print(
            "Answer human input API: PASS"
        )

        # Verify that the request is no longer pending.
        response = client.get(
            f"/api/executions/{execution_id}/human-input"
        )

        print(
            f"Get remaining pending input: "
            f"{response.status_code}"
        )

        assert response.status_code == 200

        remaining_requests = response.json()

        assert remaining_requests == []

        print(
            "Pending input cleared after answer: PASS"
        )

        print()
        print(
            "HUMAN INPUT API INTEGRATION TEST: PASS"
        )

    finally:
        # Remove only the human input request created
        # by this test.
        if human_request is not None:
            human_request_object = db.get(
                HumanInputRequest,
                UUID(
                    human_request["request_id"]
                ),
            )

            if human_request_object is not None:
                db.delete(
                    human_request_object
                )

        db.commit()
        db.close()


if __name__ == "__main__":
    main()