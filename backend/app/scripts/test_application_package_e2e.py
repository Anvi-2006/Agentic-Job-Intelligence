from backend.app.core.database import SessionLocal
from backend.app.models.candidate import CandidateProfile
from backend.app.models.job import Job
from backend.app.services.application_package_service import (
    generate_application_package,
)


def main():
    db = SessionLocal()

    try:
        candidate = db.query(CandidateProfile).first()

        if candidate is None:
            raise RuntimeError("No candidate profile found in database.")

        job = (
            db.query(Job)
            .filter(Job.company == "FinTech Labs")
            .first()
        )

        if job is None:
            raise RuntimeError("FinTech Labs job not found in database.")

        print("=" * 70)
        print("APPLICATION PACKAGE E2E TEST")
        print("=" * 70)
        print(f"Candidate ID : {candidate.id}")
        print(f"Job          : {job.company} | {job.title}")
        print(f"Job ID       : {job.id}")
        print()

        print("Generating application package...")
        print("This will make a real Gemini API request.")
        print()

        package = generate_application_package(
            db=db,
            candidate_id=candidate.id,
            job_id=job.id,
        )

        print("=" * 70)
        print("RESULT")
        print("=" * 70)

        print(f"Company          : {package['company']}")
        print(f"Job              : {package['job_title']}")
        print(f"Readiness score  : {package['readiness_score']}")
        print(f"Recommendation    : {package['recommendation']}")
        print(f"Valid             : {package['is_valid']}")
        print()

        print("TAILORED SUMMARY")
        print("-" * 70)
        print(package["tailored_summary"])
        print()

        print("COVER LETTER")
        print("-" * 70)
        print(package["cover_letter"])
        print()

        print("KEY STRENGTHS")
        print("-" * 70)
        for strength in package["key_strengths"]:
            print(f"- {strength}")
        print()

        print("MISSING REQUIREMENTS")
        print("-" * 70)
        for requirement in package["missing_requirements"]:
            print(f"- {requirement}")
        print()

        print("APPLICATION QUESTIONS")
        print("-" * 70)
        for index, item in enumerate(
            package["application_questions"],
            start=1,
        ):
            print(f"{index}. {item['question']}")
            print(f"   Answer: {item['answer']}")
            print(f"   Evidence: {item['evidence_used']}")
            print()

        print("EVIDENCE USED")
        print("-" * 70)
        for evidence in package["evidence_used"]:
            print(f"- {evidence}")
        print()

        print("VALIDATION ISSUES")
        print("-" * 70)
        if package["unsupported_claims"]:
            for issue in package["unsupported_claims"]:
                print(f"- {issue}")
        else:
            print("None")

        print()
        print("=" * 70)

        if package["is_valid"]:
            print("E2E TEST PASSED")
        else:
            print("E2E TEST COMPLETED — PACKAGE REQUIRES REVIEW")

    finally:
        db.close()


if __name__ == "__main__":
    main()
