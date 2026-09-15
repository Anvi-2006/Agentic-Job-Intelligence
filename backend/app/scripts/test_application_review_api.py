from fastapi.testclient import TestClient

from backend.app.core.database import SessionLocal
from backend.app.main import app
from backend.app.models.application import Application
from backend.app.models.application_package import ApplicationPackage
from backend.app.models.candidate import CandidateProfile
from backend.app.models.job import Job


client = TestClient(app)


def main():
    db = SessionLocal()

    try:
        candidate = db.query(CandidateProfile).first()

        if candidate is None:
            raise RuntimeError("No candidate profile found.")

        job = (
            db.query(Job)
            .filter(Job.company == "FinTech Labs")
            .first()
        )

        if job is None:
            raise RuntimeError("FinTech Labs job not found.")

        application = (
            db.query(Application)
            .filter(
                Application.candidate_id == candidate.id,
                Application.job_id == job.id,
            )
            .first()
        )

        if application is None:
            raise RuntimeError(
                "No application found for the test candidate/job."
            )

        application_package = (
            db.query(ApplicationPackage)
            .filter(
                ApplicationPackage.application_id == application.id,
            )
            .first()
        )

        if application_package is None:
            raise RuntimeError(
                "No application package found for the test application."
            )

        candidate_id = str(candidate.id)
        job_id = str(job.id)

        original_status = application.status
        original_note = application.reviewer_note
        original_package_valid = application_package.is_valid

        print("=" * 70)
        print("APPLICATION REVIEW SAFETY TEST")
        print("=" * 70)
        print()

        # ---------------------------------------------------------------
        # Test setup
        # ---------------------------------------------------------------
        application.status = "pending_review"
        application.reviewer_note = None
        application_package.is_valid = False
        db.commit()

        # ---------------------------------------------------------------
        # 1. Invalid package -> approval must fail
        # ---------------------------------------------------------------
        response = client.post(
            f"/api/applications/{candidate_id}/{job_id}/review",
            json={
                "decision": "APPROVED",
                "reviewer_note": "This approval should be blocked.",
            },
        )

        print("TEST 1: invalid package -> approved")
        print("-" * 70)
        print("Status code :", response.status_code)

        assert response.status_code == 400, response.text

        error = response.json()

        assert (
            "application package is invalid"
            in error["detail"].lower()
        )

        db.refresh(application)

        assert application.status == "pending_review"

        print("Result      : PASS")
        print("Approval correctly blocked.")
        print()

        # ---------------------------------------------------------------
        # 2. Valid package -> approval must succeed
        # ---------------------------------------------------------------
        application_package.is_valid = True
        db.commit()

        response = client.post(
            f"/api/applications/{candidate_id}/{job_id}/review",
            json={
                "decision": "APPROVED",
                "reviewer_note": "Application package approved for next step.",
            },
        )

        print("TEST 2: valid package -> approved")
        print("-" * 70)
        print("Status code :", response.status_code)

        assert response.status_code == 200, response.text

        data = response.json()

        assert data["candidate_id"] == candidate_id
        assert data["job_id"] == job_id
        assert data["company"] == "FinTech Labs"
        assert data["status"] == "approved"
        assert (
            data["reviewer_note"]
            == "Application package approved for next step."
        )

        print("Result      : PASS")
        print("Status      :", data["status"])
        print()

        # ---------------------------------------------------------------
        # 3. Approved -> rejected must fail
        # ---------------------------------------------------------------
        response = client.post(
            f"/api/applications/{candidate_id}/{job_id}/review",
            json={
                "decision": "REJECTED",
                "reviewer_note": "This transition should not be allowed.",
            },
        )

        print("TEST 3: approved -> rejected")
        print("-" * 70)
        print("Status code :", response.status_code)

        assert response.status_code == 400, response.text

        error = response.json()

        assert "Invalid application state transition" in error["detail"]

        print("Result      : PASS")
        print("Terminal state correctly protected.")
        print()

        # ---------------------------------------------------------------
        # 4. Tracker must still show approved
        # ---------------------------------------------------------------
        response = client.get(
            f"/api/applications/{candidate_id}"
        )

        print("TEST 4: tracker preserves approved state")
        print("-" * 70)
        print("Status code :", response.status_code)

        assert response.status_code == 200, response.text

        tracker = response.json()

        assert tracker["candidate_id"] == candidate_id
        assert tracker["total_applications"] >= 1

        tracked_application = next(
            item
            for item in tracker["applications"]
            if item["job_id"] == job_id
        )

        assert tracked_application["status"] == "approved"

        print("Result      : PASS")
        print("Tracked status:", tracked_application["status"])
        print()

        # ---------------------------------------------------------------
        # Restore original database state
        # ---------------------------------------------------------------
        application.status = original_status
        application.reviewer_note = original_note
        application_package.is_valid = original_package_valid
        db.commit()

        print("=" * 70)
        print("APPLICATION REVIEW SAFETY TEST PASSED")
        print("=" * 70)

    finally:
        db.close()


if __name__ == "__main__":
    main()