from urllib.parse import urlparse
from urllib.request import Request, urlopen


def verify_job(job: dict) -> dict:
    source = (job.get("source") or "").lower()
    url = job.get("job_url")
    company = (job.get("company") or "").lower()

    if source == "demo":
        return {
            "verification_status": "UNVERIFIED",
            "verification_confidence": 0.0,
            "verification_reason": "Demo job; source has not been externally verified.",
        }

    if not url:
        return {
            "verification_status": "UNVERIFIED",
            "verification_confidence": 0.0,
            "verification_reason": "No application URL is available.",
        }

    try:
        request = Request(
            url,
            headers={"User-Agent": "ApplyIQ/1.0"},
            method="HEAD",
        )

        with urlopen(request, timeout=5) as response:
            if not 200 <= response.status < 400:
                raise ValueError("URL is not reachable")

        hostname = (urlparse(url).hostname or "").lower()
        company_tokens = [
            token
            for token in company.replace("-", " ").split()
            if len(token) >= 4
        ]

        official = any(token in hostname for token in company_tokens)

        if official:
            return {
                "verification_status": "OFFICIAL_SOURCE",
                "verification_confidence": 0.90,
                "verification_reason": "Application link is reachable and matches the company's domain.",
            }

        if source in {"greenhouse", "lever"}:
            return {
                "verification_status": "VERIFIED_SOURCE",
                "verification_confidence": 0.85,
                "verification_reason": f"Application link is reachable and the job was retrieved from the {source.title()} job-posting source.",
            }

        return {
            "verification_status": "LINK_REACHABLE",
            "verification_confidence": 0.60,
            "verification_reason": "Application link is reachable, but the company domain could not be confirmed.",
        }

    except Exception:
        return {
            "verification_status": "UNVERIFIED",
            "verification_confidence": 0.0,
            "verification_reason": "Application link could not be verified.",
        }