import re


def _find_spacing_issues(text: str) -> list[str]:
    issues = []

    if not text:
        return issues

    # Missing space after punctuation.
    if re.search(r"[,;:!?][A-Za-z]", text):
        issues.append("missing space after punctuation")

    # Detect common word concatenation patterns without
    # treating legitimate CamelCase technical names as errors.
    concatenation_patterns = [
        r"\b[A-Za-z]{2,}(?:and|or|using|with|for|to|of|in|as)[A-Z][a-z]+",
        r"\b(?:and|or|using|with|for|to|of|in|as)(?:Python|FastAPI|PostgreSQL|LangChain|Streamlit|BeautifulSoup)\b",
    ]

    for pattern in concatenation_patterns:
        if re.search(pattern, text):
            issues.append("missing space between words")

    # Spaces accidentally inserted before punctuation.
    if re.search(r"\s+([,.;:!?])", text):
        issues.append("space before punctuation")

    return list(dict.fromkeys(issues))


def _find_repeated_spaces(text: str) -> list[str]:
    if re.search(r"[ \t]{2,}", text):
        return ["repeated spaces"]

    return []


def _find_repeated_words(text: str) -> list[str]:
    words = re.findall(r"\b[A-Za-z]+\b", text.lower())

    repeated = []

    for first, second in zip(words, words[1:]):
        if first == second:
            repeated.append(f"repeated word: {first}")

    return repeated


def _find_unprofessional_patterns(text: str) -> list[str]:
    issues = []

    if not text:
        return issues

    patterns = {
        "placeholder company": r"\bCompany Name\b",
        "placeholder role": r"\bJob Title\b",
        "placeholder text": r"\bLorem ipsum\b",
        "placeholder candidate name": (
            r"\[(?:candidate\s+name|name|your\s+name)\]"
            r"|\bYour Name\b"
        ),
    }

    for issue_name, pattern in patterns.items():
        if re.search(pattern, text, re.IGNORECASE):
            issues.append(issue_name)

    return issues


def _validate_text_quality(text: str) -> list[str]:
    issues = []

    issues.extend(_find_spacing_issues(text))
    issues.extend(_find_repeated_spaces(text))
    issues.extend(_find_repeated_words(text))
    issues.extend(_find_unprofessional_patterns(text))

    return list(dict.fromkeys(issues))


def validate_application_quality(
    package: dict,
    candidate_name: str | None = None,
) -> dict:
    issues = []
    if candidate_name:
        cover_letter = package.get("cover_letter", "")

        if isinstance(cover_letter, str):
            signature_pattern = r"(?i)\bsincerely,\s*([^\n]+)"

            match = re.search(signature_pattern, cover_letter)

            if match:
                signature_name = match.group(1).strip()

                if signature_name != candidate_name.strip():
                    issues.append(
                        "cover_letter: incorrect candidate name in signature"
                    )
            else:
                issues.append(
                    "cover_letter: missing candidate signature"
                )
    cover_letter = package.get("cover_letter", "")
    tailored_summary = package.get("tailored_summary", "")
    strengths = package.get("key_strengths", [])
    questions = package.get("application_questions", [])

    if isinstance(cover_letter, str):
        issues.extend(
            f"cover_letter: {issue}"
            for issue in _validate_text_quality(cover_letter)
        )

    if isinstance(tailored_summary, str):
        issues.extend(
            f"tailored_summary: {issue}"
            for issue in _validate_text_quality(tailored_summary)
        )

    if isinstance(strengths, list):
        for index, strength in enumerate(strengths):
            if isinstance(strength, str):
                issues.extend(
                    f"key_strengths[{index}]: {issue}"
                    for issue in _validate_text_quality(strength)
                )

    if isinstance(questions, list):
        for index, item in enumerate(questions):
            if not isinstance(item, dict):
                continue

            question = item.get("question", "")
            answer = item.get("answer", "")

            if isinstance(question, str):
                issues.extend(
                    f"question[{index}]: {issue}"
                    for issue in _validate_text_quality(question)
                )

            if isinstance(answer, str):
                issues.extend(
                    f"answer[{index}]: {issue}"
                    for issue in _validate_text_quality(answer)
                )

    return {
        "is_valid": len(issues) == 0,
        "quality_issues": list(dict.fromkeys(issues)),
    }