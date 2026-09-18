import json
import re

from google import genai
from backend.app.core.config import settings
from backend.app.schemas.resume import CandidateResume


client = genai.Client(api_key=settings.gemini_api_key)

def _normalize_candidate_signature(
    cover_letter: str,
    candidate_name: str,
) -> str:
    """
    Ensure a generated cover letter does not contain a generic
    placeholder candidate name in its signature.

    The candidate name comes from the verified candidate record,
    so replacing known placeholders is deterministic and safe.
    """
    if not cover_letter or not candidate_name.strip():
        return cover_letter

    verified_name = candidate_name.strip()

    placeholder_names = {
        "candidate",
        "applicant",
        "your name",
        "[name]",
        "[your name]",
        "[candidate name]",
    }

    pattern = re.compile(
        r"(?im)^(\s*Sincerely,\s*)([^\n]+)\s*$"
    )

    def replace_signature(match: re.Match) -> str:
        prefix = match.group(1)
        signature_name = match.group(2).strip()

        if signature_name.lower() in placeholder_names:
            return f"{prefix}{verified_name}"

        return match.group(0)

    return pattern.sub(replace_signature, cover_letter)

def _normalize_generated_text(text: str) -> str:
    """
    Normalize safe formatting artifacts from LLM-generated text
    without modifying technical names or CamelCase identifiers.
    """
    if not text:
        return ""

    text = text.replace("\u00a0", " ")

    # Fix missing spaces after punctuation.
    text = re.sub(r"([,;:])([A-Za-z])", r"\1 \2", text)

    # Fix spaces accidentally inserted before punctuation.
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)

    # Collapse repeated spaces while preserving newlines.
    text = re.sub(r"[ \t]+", " ", text)

    # Normalize excessive blank lines.
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()

def generate_search_intent_fallback(user_goal: str) -> dict:
    """
    Local fallback for job-search intent extraction.

    Used when Gemini is unavailable, rate-limited,
    or returns an invalid response.
    """

    text = user_goal.lower()

    roles = []
    locations = []
    skills = []

    # Roles
    role_keywords = [
        "backend",
        "frontend",
        "full stack",
        "software engineer",
        "software developer",
        "ai engineer",
        "machine learning engineer",
        "data scientist",
    ]

    for role in role_keywords:
        if role in text:
            roles.append(role)

    # Locations
    location_keywords = [
        "pune",
        "mumbai",
        "bangalore",
        "bengaluru",
        "delhi",
        "hyderabad",
        "chennai",
        "remote",
    ]

    for location in location_keywords:
        if location in text:
            locations.append(location)

    # Skills
    skill_keywords = [
        "python",
        "java",
        "c++",
        "javascript",
        "typescript",
        "react",
        "fastapi",
        "django",
        "node.js",
        "sql",
        "postgresql",
        "mongodb",
        "docker",
        "aws",
        "machine learning",
        "deep learning",
    ]

    for skill in skill_keywords:
        if skill in text:
            skills.append(skill)

    # Experience level
    experience_level = None

    if "internship" in text or "intern" in text:
        experience_level = "internship"
    elif "entry-level" in text or "fresher" in text:
        experience_level = "entry-level"
    elif "senior" in text:
        experience_level = "senior"
    elif "mid-level" in text:
        experience_level = "mid-level"

    # Work mode
    work_mode = None

    if "remote" in text:
        work_mode = "remote"
    elif "hybrid" in text:
        work_mode = "hybrid"
    elif "onsite" in text or "on-site" in text:
        work_mode = "onsite"

    # Employment type
    employment_type = None

    if "internship" in text or "intern" in text:
        employment_type = "internship"
    elif "full-time" in text or "full time" in text:
        employment_type = "full-time"
    elif "part-time" in text or "part time" in text:
        employment_type = "part-time"

    return {
        "roles": roles,
        "locations": locations,
        "experience_level": experience_level,
        "work_mode": work_mode,
        "employment_type": employment_type,
        "skills": skills,
        "company_preferences": [],
    }


def generate_search_intent(user_goal: str) -> dict:
    """
    Convert a job search request into structured search intent.
    Uses a fast path for simple searches and Gemini for complex requests.
    """

    query = user_goal.strip()

    # Fast path for simple job-role searches
    if query and len(query.split()) <= 4:
        return {
            "roles": [query.lower()],
            "locations": [],
            "experience_level": None,
            "work_mode": None,
            "employment_type": None,
            "skills": [],
            "company_preferences": [],
        }

    prompt = f"""
You are a job-search intent extraction assistant.

Convert the user's job search request into structured JSON.

USER REQUEST:
{query}

Extract:

- roles: job roles the user is looking for
- locations: preferred cities, countries, or remote
- experience_level: internship, entry-level, mid-level, senior, etc.
- work_mode: remote, hybrid, onsite, or null
- employment_type: internship, full-time, part-time, contract, or null
- skills: skills or technologies explicitly mentioned
- company_preferences: company types, names, industries, or preferences explicitly mentioned

STRICT RULES:

1. Extract only information supported by the user's request.
2. Do not invent preferences.
3. Do not assume a location if none is provided.
4. Do not assume experience level if none is provided.
5. Return ONLY valid JSON.
6. Use empty arrays when no values are available.
7. Use null when a single-value field is not specified.

Return exactly this structure:

{{
    "roles": [],
    "locations": [],
    "experience_level": null,
    "work_mode": null,
    "employment_type": null,
    "skills": [],
    "company_preferences": []
}}
"""

    try:
        interaction = client.interactions.create(
            model="gemini-3.6-flash",
            input=prompt,
            generation_config={
                "thinking_level": "low",
            },
        )

        response_text = interaction.output_text

        if not response_text:
            raise RuntimeError(
                "Gemini returned an empty search intent"
            )

        response_text = response_text.strip()

        if response_text.startswith("```"):
            response_text = response_text.removeprefix("```json")
            response_text = response_text.removeprefix("```")
            response_text = response_text.removesuffix("```")
            response_text = response_text.strip()

        start = response_text.find("{")
        end = response_text.rfind("}")

        if start == -1 or end == -1 or start > end:
            raise RuntimeError(
                "Gemini returned invalid JSON for search intent"
            )

        json_text = response_text[start:end + 1]

        try:
            return json.loads(json_text)

        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Gemini returned invalid JSON for search intent"
            ) from exc

    except Exception:
        return generate_search_intent_fallback(query)

def generate_resume_tailoring(
    job_title: str,
    company: str,
    job_requirements: list[str],
    candidate_evidence: list[dict],
    missing_requirements: list[str],
) -> str:
    """
    Generate an evidence-grounded tailored resume summary.
    """

    evidence_text = "\n".join(
        [
            (
                f"- [{item['category']}] "
                f"{item['title']}: "
                f"{item['content']}"
            )
            for item in candidate_evidence
        ]
    )

    requirements_text = "\n".join(
        f"- {requirement}"
        for requirement in job_requirements
    )

    missing_requirements_text = "\n".join(
        f"- {requirement}"
        for requirement in missing_requirements
    )

    prompt = f"""
You are an evidence-grounded resume tailoring assistant.

Your task is to tailor a candidate's resume content for a specific job.

STRICT RULES:

1. Use ONLY information present in the candidate evidence.
2. Do NOT invent skills, projects, achievements, experience,
   companies, technologies, metrics, or responsibilities.
3. Do NOT claim that the candidate possesses a missing job requirement.
4. Treat every requirement listed as missing as unsupported.
5. Do NOT use synonyms, hyphenated forms, or indirect wording
   to claim a missing requirement.
6. You may improve wording and ordering of verified information.
7. Keep the content truthful and professional.
8. Prefer evidence that is directly relevant to the target job.
9. If evidence is insufficient, omit the claim rather than inventing it.
10. Never turn a job requirement into a candidate skill unless
    verified evidence supports it.

TARGET JOB:

Title: {job_title}
Company: {company}

JOB REQUIREMENTS:

{requirements_text}

VERIFIED CANDIDATE EVIDENCE:

{evidence_text}

IMPORTANT:

The candidate's missing requirements are explicitly listed below.
You MUST NOT claim or imply that the candidate has these skills.

MISSING REQUIREMENTS:

{missing_requirements_text}

Generate a tailored resume summary.

The summary should:

- be concise and grammatically correct
- be professional and natural
- use clear spacing and punctuation
- use standard professional English
- emphasize verified relevant skills
- mention relevant project experience only when supported by evidence
- avoid unsupported claims
- be easy for a recruiter to read

Return ONLY the resume summary text.
"""

    interaction = client.interactions.create(
        model="gemini-3.6-flash",
        input=prompt,
        generation_config={
            "thinking_level": "low",
        },
    )

    summary = interaction.output_text

    if not summary:
        raise RuntimeError(
            "Gemini returned an empty resume summary"
        )

    summary = _normalize_generated_text(summary)

    if not summary:
        raise RuntimeError(
            "Gemini returned an empty resume summary after normalization"
        )

    return summary



def generate_complete_application_package(
    job_title: str,
    company: str,
    job_requirements: list[str],
    candidate_name: str,
    job_description: str,
    candidate_evidence: list[dict],
    matched_requirements: list[dict],
    missing_requirements: list[str],
) -> dict:
    """
    Generate the complete evidence-grounded application package
    in a single Gemini call.
    """

    evidence_text = "\n".join(
        [
            (
                f"- [{item['category']}] "
                f"{item['title']}: "
                f"{item['content']}"
            )
            for item in candidate_evidence
        ]
    )

    requirements_text = "\n".join(
        f"- {requirement}"
        for requirement in job_requirements
    )

    matched_text = "\n".join(
        [
            (
                f"- Requirement: {item['requirement']}\n"
                f"  Match status: {item['match_status']}\n"
                f"  Evidence IDs: "
                f"{', '.join(item.get('evidence_ids', []))}"
            )
            for item in matched_requirements
            if item.get("match_status") in {
                "matched",
                "partial",
            }
        ]
    )

    missing_text = "\n".join(
        f"- {requirement}"
        for requirement in missing_requirements
    )

    prompt = f"""
You are an evidence-grounded job application assistant.

Your task is to prepare a complete application package for a
candidate applying to a specific job.

The VERIFIED CANDIDATE EVIDENCE below is the complete and exclusive
source of truth for all candidate-specific claims.

You MUST NOT use information outside this evidence.

TARGET JOB

Company: {company}
Job Title: {job_title}

JOB DESCRIPTION

{job_description}

JOB REQUIREMENTS

{requirements_text}

REQUIREMENT-TO-EVIDENCE MAPPING

{matched_text}

MISSING REQUIREMENTS

{missing_text}

VERIFIED CANDIDATE NAME

{candidate_name}

VERIFIED CANDIDATE EVIDENCE

{evidence_text}

STRICT TRUTHFULNESS RULES

1. Use ONLY information present in VERIFIED CANDIDATE EVIDENCE.
2. Never invent skills, projects, companies, roles, technologies,
   responsibilities, achievements, education, certifications,
   metrics, dates, or experience.
3. Never claim that the candidate has a missing requirement.
4. Never imply experience with a missing requirement.
5. Never invent years of experience.
6. Never invent percentages, numbers, rankings, or measurable results.
7. Never invent employment experience from academic or personal projects.
8. Never turn a job requirement into a candidate skill.
9. You may paraphrase verified evidence.
10. You may improve grammar and presentation.
11. If evidence is insufficient, omit the claim.
12. Every generated section must be grounded in verified evidence.
13. Do not mention internal evidence IDs in candidate-facing text.
14. evidence_used must contain ONLY evidence titles appearing in
    VERIFIED CANDIDATE EVIDENCE.
15. Generate exactly 3 application questions.
16. Generate between 3 and 5 key strengths.
17. Each application-question answer must use at least one fact
    supported by its declared evidence.
18. Do not include a candidate-specific claim unless the evidence
    supports it.
19. Keep application answers concise and specific.
20. Preserve normal spaces between words.
21. Preserve normal spaces after punctuation.
22. Never concatenate adjacent words.
23. Never split, alter, or rewrite technical names appearing in
    the evidence.
24. Preserve exact spelling and capitalization of technical names.
25. Use the verified candidate name when a candidate name is required.
26. Never use placeholder names such as "Candidate", "Applicant",
    "Your Name", "[Name]", or similar placeholders.
27. Do not add information simply to make the candidate sound stronger.

TAILORED RESUME SUMMARY

Create a concise professional resume summary specifically
relevant to this job.

The summary should:

- emphasize verified relevant skills
- mention relevant project experience only when supported
- avoid unsupported claims
- be recruiter-friendly
- remain truthful
- not claim missing requirements

COVER LETTER

Write a concise professional cover letter tailored to the job.

Use only verified candidate evidence.

The signature must use the verified candidate name.

KEY STRENGTHS

Return 3 to 5 strengths directly supported by the evidence.

APPLICATION QUESTIONS

Generate exactly 3 realistic application or interview questions
relevant to this job.

For every question:

- provide a concise answer
- use only verified candidate evidence
- list the exact evidence titles used
- do not invent information

Return ONLY valid JSON.

Return exactly this structure:

{{
  "tailored_summary": "string",
  "cover_letter": "string",
  "key_strengths": [
    "string"
  ],
  "application_questions": [
    {{
      "question": "string",
      "answer": "string",
      "evidence_used": [
        "exact evidence title"
      ]
    }}
  ]
}}
"""

    interaction = client.interactions.create(
        model="gemini-3.6-flash",
        input=prompt,
        generation_config={
            "thinking_level": "low",
        },
    )

    response_text = interaction.output_text

    if not response_text:
        raise RuntimeError(
            "Gemini returned an empty application package"
        )

    response_text = response_text.strip()

    if response_text.startswith("```"):
        response_text = response_text.removeprefix("```json")
        response_text = response_text.removeprefix("```")
        response_text = response_text.removesuffix("```")
        response_text = response_text.strip()

    start = response_text.find("{")
    end = response_text.rfind("}")

    if start == -1 or end == -1 or start > end:
        raise RuntimeError(
            "Gemini returned invalid JSON for the complete application package"
        )

    json_text = response_text[start:end + 1]

    try:
        parsed = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Gemini returned invalid JSON for the complete application package"
        ) from exc

    if not isinstance(parsed, dict):
        raise RuntimeError(
            "Gemini application package must be a JSON object"
        )

    required_fields = {
        "tailored_summary",
        "cover_letter",
        "key_strengths",
        "application_questions",
    }

    missing_fields = required_fields - parsed.keys()

    if missing_fields:
        raise RuntimeError(
            "Gemini application package is missing fields: "
            + ", ".join(sorted(missing_fields))
        )

    if not isinstance(parsed["tailored_summary"], str):
        raise RuntimeError(
            "Gemini tailored_summary must be a string"
        )

    if not isinstance(parsed["cover_letter"], str):
        raise RuntimeError(
            "Gemini cover_letter must be a string"
        )

    if not isinstance(parsed["key_strengths"], list):
        raise RuntimeError(
            "Gemini key_strengths must be a list"
        )

    if not isinstance(parsed["application_questions"], list):
        raise RuntimeError(
            "Gemini application_questions must be a list"
        )

    if not parsed["tailored_summary"].strip():
        raise RuntimeError(
            "Gemini tailored_summary cannot be empty"
        )

    if not parsed["cover_letter"].strip():
        raise RuntimeError(
            "Gemini cover_letter cannot be empty"
        )

    if len(parsed["key_strengths"]) < 3:
        raise RuntimeError(
            "Gemini application package must contain at least 3 key strengths"
        )

    if len(parsed["key_strengths"]) > 5:
        raise RuntimeError(
            "Gemini application package must contain at most 5 key strengths"
        )

    if len(parsed["application_questions"]) != 3:
        raise RuntimeError(
            "Gemini application package must contain exactly 3 application questions"
        )

    parsed["tailored_summary"] = _normalize_generated_text(
        parsed["tailored_summary"]
    )

    parsed["cover_letter"] = _normalize_generated_text(
        parsed["cover_letter"]
    )

    parsed["cover_letter"] = _normalize_candidate_signature(
        cover_letter=parsed["cover_letter"],
        candidate_name=candidate_name,
    )

    normalized_strengths = []

    for strength in parsed["key_strengths"]:
        if not isinstance(strength, str):
            raise RuntimeError(
                "Gemini key strengths must contain only strings"
            )

        normalized_strength = _normalize_generated_text(
            strength
        )

        if normalized_strength:
            normalized_strengths.append(
                normalized_strength
            )

    if len(normalized_strengths) < 3:
        raise RuntimeError(
            "Gemini application package contains fewer than 3 valid strengths"
        )

    parsed["key_strengths"] = normalized_strengths

    normalized_questions = []

    for item in parsed["application_questions"]:

        if not isinstance(item, dict):
            raise RuntimeError(
                "Each application question must be an object"
            )

        required_question_fields = {
            "question",
            "answer",
            "evidence_used",
        }

        missing_question_fields = (
            required_question_fields - item.keys()
        )

        if missing_question_fields:
            raise RuntimeError(
                "Application question is missing fields: "
                + ", ".join(sorted(missing_question_fields))
            )

        if not isinstance(item["question"], str):
            raise RuntimeError(
                "Application question must be a string"
            )

        if not isinstance(item["answer"], str):
            raise RuntimeError(
                "Application answer must be a string"
            )

        if not isinstance(item["evidence_used"], list):
            raise RuntimeError(
                "Application question evidence_used must be a list"
            )

        item["question"] = _normalize_generated_text(
            item["question"]
        )

        item["answer"] = _normalize_generated_text(
            item["answer"]
        )

        item["evidence_used"] = [
            evidence_title.strip()
            for evidence_title in item["evidence_used"]
            if isinstance(evidence_title, str)
            and evidence_title.strip()
        ]

        if not item["question"] or not item["answer"]:
            raise RuntimeError(
                "Application question and answer cannot be empty"
            )

        if not item["evidence_used"]:
            raise RuntimeError(
                "Every application question must reference evidence"
            )

        normalized_questions.append(item)

    parsed["application_questions"] = normalized_questions

    return parsed

def generate_application_package(
    job_title: str,
    company: str,
    candidate_name: str,
    job_description: str,
    candidate_evidence: list[dict],
    matched_requirements: list[dict],
    missing_requirements: list[str],
    tailored_summary: str,
) -> dict:
    """
    Generate an evidence-grounded application package.

    Gemini may improve wording, but it must only use
    verified candidate evidence.
    """

    evidence_text = "\n".join(
        [
            (
                f"- [{item['category']}] "
                f"{item['title']}: "
                f"{item['content']}"
            )
            for item in candidate_evidence
        ]
    )

    matched_text = "\n".join(
        [
            (
                f"- Requirement: {item['requirement']}\n"
                f"  Match status: {item['match_status']}\n"
                f"  Evidence IDs: "
                f"{', '.join(item.get('evidence_ids', []))}"
            )
            for item in matched_requirements
            if item.get("match_status") in {
                "matched",
                "partial",
            }
        ]
    )

    missing_text = "\n".join(
        f"- {requirement}"
        for requirement in missing_requirements
    )

    prompt = f"""
You are an evidence-grounded job application assistant.

Your task is to prepare an application package for a candidate.

IMPORTANT:
The VERIFIED CANDIDATE EVIDENCE below is the complete and exclusive
source of truth for candidate-specific claims.

You MUST NOT use information outside this evidence.

TARGET JOB

Company: {company}
Job Title: {job_title}

VERIFIED CANDIDATE NAME

{candidate_name}

JOB DESCRIPTION

{job_description}

REQUIREMENT-TO-EVIDENCE MAPPING

{matched_text}

MISSING REQUIREMENTS

{missing_text}

VERIFIED CANDIDATE EVIDENCE

{evidence_text}

TAILORED RESUME SUMMARY

{tailored_summary}

STRICT TRUTHFULNESS RULES

1. Use ONLY information present in VERIFIED CANDIDATE EVIDENCE.
2. Never invent skills, projects, companies, roles, technologies,
   responsibilities, achievements, education, certifications,
   metrics, dates, or experience.
3. Never claim that the candidate has a missing requirement.
4. Never imply experience with a missing requirement.
5. Never invent years of experience.
6. Never invent percentages, numbers, rankings, or measurable results.
7. Never invent employment experience from academic or personal projects.
8. Never turn a job requirement into a candidate skill.
9. You may paraphrase verified evidence.
10. You may improve grammar and presentation.
11. If evidence is insufficient, omit the claim.
12. Every application-question answer must be grounded in the
    VERIFIED CANDIDATE EVIDENCE.
13. evidence_used must contain ONLY evidence titles that appear
    in VERIFIED CANDIDATE EVIDENCE.
14. Generate exactly 3 application questions.
15. Generate between 3 and 5 key strengths.
16. Do not mention internal evidence IDs in the cover letter or answers.
17. Do not add information because it would make the candidate
    sound stronger.
18. Each application-question answer must use at least one fact
    that is directly supported by the evidence titles listed for that answer.
19. Do not include a candidate-specific claim in an answer unless the
    listed evidence supports that claim.
20. Keep each answer concise and specific to the question.
21. Preserve normal spaces between every word.
22. Preserve normal spaces after commas, periods, colons, and other punctuation.
23. Never concatenate adjacent words.
24. Never split, alter, or rewrite technical names such as FastAPI,
    PostgreSQL, ResearchMind, LangChain, BeautifulSoup, Streamlit,
    Python, GitHub, or other proper names appearing in the evidence.
25. Preserve the exact spelling and capitalization of technical names
    from the verified candidate evidence.
26. The VERIFIED CANDIDATE NAME above is the only valid candidate name.
27. If you include a signature, use that exact candidate name.
28. Never use "Candidate", "Applicant", "Your Name", "ResearchMind",
    a project name, or any other placeholder or evidence title as the candidate name.
29. Never invent, modify, abbreviate, or replace the verified candidate name.
    
COVER LETTER

Write a concise professional cover letter.

Use only verified candidate evidence.

KEY STRENGTHS

Return 3 to 5 strengths directly supported by the evidence.

APPLICATION QUESTIONS

Generate exactly 3 realistic application or interview questions
relevant to this job.

For every question:

- provide a concise answer
- use only verified candidate evidence
- list the exact evidence titles used
- do not invent information

Return ONLY valid JSON.

Return exactly this structure:

{{
  "cover_letter": "string",
  "key_strengths": [
    "string"
  ],
  "application_questions": [
    {{
      "question": "string",
      "answer": "string",
      "evidence_used": [
        "exact evidence title"
      ]
    }}
  ]
}}
"""

    interaction = client.interactions.create(
        model="gemini-3.6-flash",
        input=prompt,
        generation_config={
            "thinking_level": "low",
        },
    )

    response_text = interaction.output_text

    if not response_text:
        raise RuntimeError(
            "Gemini returned an empty application package"
        )

    response_text = response_text.strip()

    # Remove Markdown code fences if Gemini adds them
    if response_text.startswith("```"):
        response_text = response_text.removeprefix("```json")
        response_text = response_text.removeprefix("```")
        response_text = response_text.removesuffix("```")
        response_text = response_text.strip()

    # Handle accidental text before or after the JSON object
    start = response_text.find("{")
    end = response_text.rfind("}")

    if start == -1 or end == -1 or start > end:
        raise RuntimeError(
            "Gemini returned invalid JSON for the application package"
        )

    json_text = response_text[start:end + 1]

    try:
        parsed = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Gemini returned invalid JSON for the application package"
        ) from exc

    if not isinstance(parsed, dict):
        raise RuntimeError(
            "Gemini application package must be a JSON object"
        )

    required_fields = {
        "cover_letter",
        "key_strengths",
        "application_questions",
    }

    missing_fields = required_fields - parsed.keys()

    if missing_fields:
        raise RuntimeError(
            "Gemini application package is missing fields: "
            + ", ".join(sorted(missing_fields))
        )

    if not isinstance(parsed["cover_letter"], str):
        raise RuntimeError(
            "Gemini cover_letter must be a string"
        )

    if not isinstance(parsed["key_strengths"], list):
        raise RuntimeError(
            "Gemini key_strengths must be a list"
        )

    if not isinstance(parsed["application_questions"], list):
        raise RuntimeError(
            "Gemini application_questions must be a list"
        )

    if len(parsed["key_strengths"]) < 3:
        raise RuntimeError(
            "Gemini application package must contain at least 3 key strengths"
        )

    if len(parsed["key_strengths"]) > 5:
        raise RuntimeError(
            "Gemini application package must contain at most 5 key strengths"
        )

    if len(parsed["application_questions"]) != 3:
        raise RuntimeError(
            "Gemini application package must contain exactly 3 application questions"
        )

    parsed["cover_letter"] = _normalize_generated_text(
        parsed["cover_letter"]
    )

    normalized_strengths = []

    for strength in parsed["key_strengths"]:
        if not isinstance(strength, str):
            raise RuntimeError(
                "Gemini key strengths must contain only strings"
            )

        normalized_strength = _normalize_generated_text(strength)

        if normalized_strength:
            normalized_strengths.append(normalized_strength)

    parsed["key_strengths"] = normalized_strengths

    if len(parsed["key_strengths"]) < 3:
        raise RuntimeError(
            "Gemini application package contains fewer than 3 valid strengths"
        )

    normalized_questions = []

    for item in parsed["application_questions"]:
        if not isinstance(item, dict):
            raise RuntimeError(
                "Each application question must be an object"
            )

        required_question_fields = {
            "question",
            "answer",
            "evidence_used",
        }

        missing_question_fields = (
            required_question_fields - item.keys()
        )

        if missing_question_fields:
            raise RuntimeError(
                "Application question is missing fields: "
                + ", ".join(sorted(missing_question_fields))
            )

        if not isinstance(item["question"], str):
            raise RuntimeError(
                "Application question must be a string"
            )

        if not isinstance(item["answer"], str):
            raise RuntimeError(
                "Application answer must be a string"
            )

        if not isinstance(item["evidence_used"], list):
            raise RuntimeError(
                "Application question evidence_used must be a list"
            )

        item["question"] = _normalize_generated_text(
            item["question"]
        )

        item["answer"] = _normalize_generated_text(
            item["answer"]
        )

        item["evidence_used"] = [
            evidence_title.strip()
            for evidence_title in item["evidence_used"]
            if isinstance(evidence_title, str)
            and evidence_title.strip()
        ]

        if not item["question"] or not item["answer"]:
            raise RuntimeError(
                "Application question and answer cannot be empty"
            )

        if not item["evidence_used"]:
            raise RuntimeError(
                "Every application question must reference evidence"
            )

        normalized_questions.append(item)

    parsed["application_questions"] = normalized_questions

    return parsed
        
def regenerate_application_package(
    job_title: str,
    company: str,
    candidate_name: str,
    job_description: str,
    candidate_evidence: list[dict],
    matched_requirements: list[dict],
    missing_requirements: list[str],
    tailored_summary: str,
    previous_package: dict,
    validation_issues: list[str],
) -> dict:
    """
    Regenerate the complete application package after validation failures.

    The previous package is treated as an invalid draft.
    Gemini must regenerate the complete package using only
    verified candidate evidence.
    """

    evidence_text = "\n".join(
        [
            (
                f"- [{item['category']}] "
                f"{item['title']}: "
                f"{item['content']}"
            )
            for item in candidate_evidence
        ]
    )

    matched_text = "\n".join(
        [
            (
                f"- Requirement: {item['requirement']}\n"
                f"  Match status: {item['match_status']}\n"
                f"  Evidence IDs: "
                f"{', '.join(item.get('evidence_ids', []))}"
            )
            for item in matched_requirements
            if item.get("match_status") in {
                "matched",
                "partial",
            }
        ]
    )

    missing_text = "\n".join(
        f"- {requirement}"
        for requirement in missing_requirements
    )

    validation_text = "\n".join(
        f"- {issue}"
        for issue in validation_issues
    )

    previous_package_text = json.dumps(
        previous_package,
        ensure_ascii=False,
        indent=2,
    )

    prompt = f"""
You are repairing an invalid job application package.

The previous package failed deterministic validation.

Your task is to generate a completely NEW and corrected
application package.

Do NOT assume that any part of the previous package is correct.

VERIFIED CANDIDATE NAME

{candidate_name}

TARGET JOB

Company: {company}
Job Title: {job_title}

JOB DESCRIPTION

{job_description}

REQUIREMENT-TO-EVIDENCE MAPPING

{matched_text}

MISSING REQUIREMENTS

{missing_text}

VERIFIED CANDIDATE EVIDENCE

{evidence_text}

PREVIOUS TAILORED SUMMARY

{tailored_summary}

VALIDATION ISSUES FROM THE PREVIOUS DRAFT

{validation_text}

PREVIOUS INVALID PACKAGE

{previous_package_text}

STRICT REPAIR RULES

1. Treat the entire previous package as invalid.
2. Fix EVERY validation issue listed above.
3. Regenerate ALL package fields.
4. Use ONLY VERIFIED CANDIDATE EVIDENCE.
5. Never invent candidate-specific information.
6. Never claim a missing requirement.
7. Never imply experience with a missing requirement.
8. Never invent years, dates, metrics, rankings, team sizes,
   employment experience, or measurable achievements.
9. Never turn a job requirement into a candidate skill.
10. Preserve the exact spelling and capitalization of technical
    names from the verified evidence.
11. Preserve normal spaces between every word.
12. Preserve spaces after punctuation.
13. Never concatenate words.
14. Never use placeholder candidate names.
15. Never use a project name, technology name, company name,
    or evidence title as the candidate's name.
16. If a signature is included, it MUST use exactly:
    {candidate_name}
17. Generate a new tailored resume summary.
18. The tailored resume summary must contain only verified
    candidate information.
19. Generate exactly 3 application questions.
20. Generate between 3 and 5 key strengths.
21. Every application-question answer must be supported by
    its declared evidence_used titles.
22. evidence_used must contain only exact evidence titles.
23. Do not copy unsupported claims from the previous package.
24. Do not add information merely to make the candidate
    sound stronger.
25. Keep all generated content concise and professional.
26. Do not mention validation, repair, evidence IDs, or
    internal system details in candidate-facing text.

TAILORED RESUME SUMMARY

Create a concise professional resume summary that is relevant
to the target job while remaining completely grounded in the
verified candidate evidence.

COVER LETTER

Create a concise professional cover letter tailored to the job.

Use only verified candidate evidence.

The signature must use the verified candidate name.

KEY STRENGTHS

Return 3 to 5 strengths directly supported by the evidence.

APPLICATION QUESTIONS

Generate exactly 3 realistic application or interview questions
relevant to this job.

For every question:

- provide a concise answer
- use only verified candidate evidence
- list the exact evidence titles used
- do not invent information

Return ONLY valid JSON.

Return exactly this structure:

{{
  "tailored_summary": "string",
  "cover_letter": "string",
  "key_strengths": [
    "string"
  ],
  "application_questions": [
    {{
      "question": "string",
      "answer": "string",
      "evidence_used": [
        "exact evidence title"
      ]
    }}
  ]
}}
"""

    interaction = client.interactions.create(
        model="gemini-3.6-flash",
        input=prompt,
        generation_config={
            "thinking_level": "low",
        },
    )

    response_text = interaction.output_text

    if not response_text:
        raise RuntimeError(
            "Gemini returned an empty repaired application package"
        )

    response_text = response_text.strip()

    if response_text.startswith("```"):
        response_text = response_text.removeprefix("```json")
        response_text = response_text.removeprefix("```")
        response_text = response_text.removesuffix("```")
        response_text = response_text.strip()

    start = response_text.find("{")
    end = response_text.rfind("}")

    if start == -1 or end == -1 or start > end:
        raise RuntimeError(
            "Gemini returned invalid JSON for the repaired application package"
        )

    json_text = response_text[start:end + 1]

    try:
        parsed = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Gemini returned invalid JSON for the repaired application package"
        ) from exc

    if not isinstance(parsed, dict):
        raise RuntimeError(
            "Gemini repaired application package must be a JSON object"
        )

    required_fields = {
        "tailored_summary",
        "cover_letter",
        "key_strengths",
        "application_questions",
    }

    missing_fields = required_fields - parsed.keys()

    if missing_fields:
        raise RuntimeError(
            "Gemini repaired application package is missing fields: "
            + ", ".join(sorted(missing_fields))
        )

    if not isinstance(parsed["tailored_summary"], str):
        raise RuntimeError(
            "Gemini repaired tailored_summary must be a string"
        )

    if not isinstance(parsed["cover_letter"], str):
        raise RuntimeError(
            "Gemini repaired cover_letter must be a string"
        )

    if not isinstance(parsed["key_strengths"], list):
        raise RuntimeError(
            "Gemini repaired key_strengths must be a list"
        )

    if not isinstance(parsed["application_questions"], list):
        raise RuntimeError(
            "Gemini repaired application_questions must be a list"
        )

    if not parsed["tailored_summary"].strip():
        raise RuntimeError(
            "Gemini repaired tailored_summary cannot be empty"
        )

    if not parsed["cover_letter"].strip():
        raise RuntimeError(
            "Gemini repaired cover_letter cannot be empty"
        )

    if len(parsed["key_strengths"]) < 3:
        raise RuntimeError(
            "Gemini repaired package must contain at least 3 key strengths"
        )

    if len(parsed["key_strengths"]) > 5:
        raise RuntimeError(
            "Gemini repaired package must contain at most 5 key strengths"
        )

    if len(parsed["application_questions"]) != 3:
        raise RuntimeError(
            "Gemini repaired package must contain exactly 3 questions"
        )

    parsed["tailored_summary"] = _normalize_generated_text(
        parsed["tailored_summary"]
    )

    parsed["cover_letter"] = _normalize_generated_text(
        parsed["cover_letter"]
    )
    
    parsed["cover_letter"] = _normalize_candidate_signature(
        cover_letter=parsed["cover_letter"],
        candidate_name=candidate_name,
    )


    normalized_strengths = []

    for strength in parsed["key_strengths"]:
        if not isinstance(strength, str):
            raise RuntimeError(
                "Gemini repaired key strengths must contain only strings"
            )

        normalized_strength = _normalize_generated_text(
            strength
        )

        if normalized_strength:
            normalized_strengths.append(
                normalized_strength
            )

    parsed["key_strengths"] = normalized_strengths

    if len(parsed["key_strengths"]) < 3:
        raise RuntimeError(
            "Gemini repaired package contains fewer than 3 valid strengths"
        )

    normalized_questions = []

    for item in parsed["application_questions"]:

        if not isinstance(item, dict):
            raise RuntimeError(
                "Each repaired application question must be an object"
            )

        required_question_fields = {
            "question",
            "answer",
            "evidence_used",
        }

        missing_question_fields = (
            required_question_fields - item.keys()
        )

        if missing_question_fields:
            raise RuntimeError(
                "Repaired application question is missing fields: "
                + ", ".join(sorted(missing_question_fields))
            )

        if not isinstance(item["question"], str):
            raise RuntimeError(
                "Repaired application question must be a string"
            )

        if not isinstance(item["answer"], str):
            raise RuntimeError(
                "Repaired application answer must be a string"
            )

        if not isinstance(item["evidence_used"], list):
            raise RuntimeError(
                "Repaired application question evidence_used must be a list"
            )

        item["question"] = _normalize_generated_text(
            item["question"]
        )

        item["answer"] = _normalize_generated_text(
            item["answer"]
        )

        item["evidence_used"] = [
            evidence_title.strip()
            for evidence_title in item["evidence_used"]
            if isinstance(evidence_title, str)
            and evidence_title.strip()
        ]

        if not item["question"] or not item["answer"]:
            raise RuntimeError(
                "Repaired application question and answer cannot be empty"
            )

        if not item["evidence_used"]:
            raise RuntimeError(
                "Every repaired application question must reference evidence"
            )

        normalized_questions.append(item)

    parsed["application_questions"] = normalized_questions

    return parsed
        
def generate_structured_resume(
    sections: dict[str, str],
) -> CandidateResume:
    """
    Convert detected resume sections into a structured CandidateResume.

    The model must only extract information explicitly present in the
    provided resume text. It must not invent missing information.
    """

    sections_text = "\n\n".join(
        f"### {section.upper()}\n{content}"
        for section, content in sections.items()
        if content.strip()
    )

    prompt = f"""
You are a resume information extraction system.

Convert the provided resume text into the CandidateResume structure.

STRICT RULES:
1. Extract ONLY information explicitly present in the resume.
2. Never invent skills, companies, roles, dates, achievements, metrics,
   technologies, projects, certifications, or experience.
3. If information is missing, use null or an empty list.
4. Preserve the meaning of the candidate's original information.
5. Do not infer employment experience from projects.
6. Do not infer a technology unless it is explicitly mentioned.
7. Do not create experience entries when the resume has no experience section.
8. Return ONLY valid JSON.
9. The JSON must match the CandidateResume structure exactly.
10. For every project, use the exact field name "name". Do not use "title".
11. For every experience item, use the exact field names defined in the schema.
12. For every education item, use the exact field names defined in the schema.
13. Do not add alternative field names or extra fields.
14. Every certification MUST be an object with exactly these fields:
    "name", "issuer", "date".
15. Never represent certifications as plain strings.
16. Every project MUST be an object with exactly these fields:
    "name", "description", "technologies", "url".
17. Every experience item MUST be an object with exactly these fields:
    "company", "role", "start_date", "end_date", "description", "technologies".
18. Every education item MUST be an object with exactly these fields:
    "institution", "degree", "field_of_study", "dates", "grade".

Expected structure:

{{
  "personal_info": {{
    "name": null,
    "email": null,
    "phone": null,
    "location": null,
    "linkedin": null,
    "github": null
  }},
  "summary": null,
  "skills": [],
  "experience": [],
  "projects": [],
  "education": [],
  "certifications": [],
  "achievements": []
}}

Resume sections:

{sections_text}
"""

    response = client.interactions.create(
        model="gemini-3.6-flash",
        input=prompt,
        generation_config={
            "thinking_level": "low",
        },
    )

    raw_text = response.output_text.strip()

    if raw_text.startswith("```"):
        raw_text = re.sub(
            r"^```(?:json)?\s*|\s*```$",
            "",
            raw_text,
            flags=re.IGNORECASE,
        ).strip()

    try:
        parsed_data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Gemini returned invalid JSON while parsing the resume."
        ) from exc

    return CandidateResume.model_validate(parsed_data)