from pathlib import Path
import re

from pypdf import PdfReader


SECTION_ALIASES = {
    "summary": {
        "summary",
        "professional summary",
        "profile",
        "about",
        "about me",
        "objective",
        "career objective",
    },
    "experience": {
        "experience",
        "work experience",
        "professional experience",
        "employment",
        "employment history",
        "work history",
    },
    "projects": {
        "projects",
        "personal projects",
        "academic projects",
        "key projects",
        "project experience",
    },
    "education": {
        "education",
        "academic background",
        "educational background",
        "qualifications",
    },
    "skills": {
        "skills",
        "technical skills",
        "technical proficiencies",
        "core skills",
        "technologies",
        "tech stack",
    },
    "certifications": {
        "certifications",
        "certificates",
        "licenses & certifications",
        "courses",
    },
    "achievements": {
        "achievements",
        "accomplishments",
        "honors",
        "awards",
    },
}


def extract_resume_text(file_path: str) -> str:
    """
    Extract raw text from a PDF resume.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Resume file not found: {file_path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF resumes are supported.")

    reader = PdfReader(str(path))

    extracted_pages = []

    for page in reader.pages:
        text = page.extract_text() or ""
        extracted_pages.append(text)

    return "\n".join(extracted_pages).strip()


def normalize_line(line: str) -> str:
    """
    Normalize a single resume line for section detection.
    """

    line = line.strip().lower()
    line = re.sub(r"[^a-z0-9& ]", "", line)
    line = re.sub(r"\s+", " ", line)

    return line


def detect_sections(text: str) -> dict[str, str]:
    lines = text.splitlines()
    detected_sections = {}
    current_section = "header"
    current_content = []

    alias_to_section = {}

    for section_name, aliases in SECTION_ALIASES.items():
        for alias in aliases:
            alias_to_section[alias] = section_name

    for line in lines:
        normalized = normalize_line(line)

        if normalized in alias_to_section:
            if current_content:
                detected_sections[current_section] = "\n".join(
                    current_content
                ).strip()

            current_section = alias_to_section[normalized]
            current_content = []

        else:
            current_content.append(line)

    if current_content:
        detected_sections[current_section] = "\n".join(
            current_content
        ).strip()

    return detected_sections