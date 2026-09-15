import re


def normalize_text(value: str) -> str:
    return " ".join(
        (value or "").strip().lower().split()
    )


def _build_evidence_text(
    candidate_evidence: list[dict],
) -> str:
    return normalize_text(
        " ".join(
            f"{item.get('title', '')} "
            f"{item.get('content', '')}"
            for item in candidate_evidence
        )
    )


def _build_evidence_titles(
    candidate_evidence: list[dict],
) -> set[str]:
    return {
        normalize_text(item.get("title", ""))
        for item in candidate_evidence
    }


def _build_evidence_by_title(
    candidate_evidence: list[dict],
) -> dict[str, dict]:
    return {
        normalize_text(item.get("title", "")): item
        for item in candidate_evidence
    }


def _requirement_pattern(requirement: str) -> str:
    normalized = normalize_text(requirement)

    escaped = re.escape(normalized)

    return escaped.replace(
        r"\ ",
        r"[\s-]+",
    )


def _find_risky_claims(text: str) -> list[str]:
    """
    Detect high-risk factual claims that should require
    explicit evidence support.
    """

    risky_claims = []

    patterns = {
        "years of experience": (
            r"\b\d+\+?\s+years?\s+of\s+"
            r"(?:professional\s+|industry\s+)?experience\b"
        ),
        "professional experience duration": (
            r"\b\d+\+?\s+years?\s+"
            r"(?:professional|industry)\s+experience\b"
        ),
        "leadership experience": (
            r"\bleadership\s+experience\b"
        ),
        "team size": (
            r"\b(?:managed|led|mentored)\s+"
            r"\d+\s+(?:people|developers|engineers|members)\b"
        ),
    }

    for claim_name, pattern in patterns.items():
        if re.search(pattern, text, re.IGNORECASE):
            risky_claims.append(claim_name)

    metric_patterns = [
        r"\b\d+(?:\.\d+)?\s*%",
        r"\b\d+(?:,\d{3})+\b",
    ]

    for pattern in metric_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            risky_claims.append(
                "unverified quantitative claim"
            )
            break

    return risky_claims


def _find_missing_requirement_claims(
    text: str,
    missing_requirements: list[str],
) -> list[str]:
    unsupported = []

    for requirement in missing_requirements:
        if not requirement:
            continue

        pattern = _requirement_pattern(requirement)

        if re.search(
            rf"\b{pattern}\b",
            text,
            re.IGNORECASE,
        ):
            unsupported.append(
                f"missing requirement claimed: {requirement}"
            )

    return unsupported


def _validate_text_against_evidence(
    text: str,
    candidate_evidence: list[dict],
) -> list[str]:
    """
    Validate high-risk claims against supplied candidate evidence.

    This intentionally allows normal paraphrasing while rejecting
    unsupported high-risk factual claims.
    """

    unsupported = []

    normalized_text = normalize_text(text)
    evidence_text = _build_evidence_text(candidate_evidence)

    if not normalized_text:
        return unsupported

    risky_claims = _find_risky_claims(
        normalized_text
    )

    for claim in risky_claims:

        if claim == "unverified quantitative claim":
            numbers = re.findall(
                r"\b\d+(?:\.\d+)?\s*%|\b\d+(?:,\d{3})+\b",
                normalized_text,
            )

            if numbers:
                supported_number = any(
                    number in evidence_text
                    for number in numbers
                )

                if not supported_number:
                    unsupported.append(claim)

        elif claim in {
            "years of experience",
            "professional experience duration",
        }:
            years = re.findall(
                r"\b\d+\+?\s+years?\b",
                normalized_text,
            )

            if years:
                supported_year = any(
                    year in evidence_text
                    for year in years
                )

                if not supported_year:
                    unsupported.append(claim)

        elif claim == "leadership experience":
            if "leadership experience" not in evidence_text:
                unsupported.append(claim)

        elif claim == "team size":
            unsupported.append(claim)

    return unsupported


def _meaningful_tokens(text: str) -> set[str]:
    """
    Extract meaningful words for conservative claim checking.

    Very common generic words are ignored because their presence
    does not prove a candidate-specific claim.
    """

    stop_words = {
        "the",
        "and",
        "for",
        "with",
        "using",
        "used",
        "have",
        "has",
        "from",
        "this",
        "that",
        "into",
        "through",
        "their",
        "candidate",
        "experience",
        "skills",
        "skill",
        "ability",
        "strong",
        "proven",
        "demonstrated",
        "practical",
        "hands",
        "on",
        "development",
        "developing",
        "building",
        "built",
        "application",
        "applications",
        "project",
        "projects",
    }

    tokens = re.findall(
        r"\b[a-zA-Z][a-zA-Z0-9+#.-]*\b",
        text.lower(),
    )

    return {
        token
        for token in tokens
        if len(token) > 2
        and token not in stop_words
    }


def _validate_strength(
    strength: str,
    candidate_evidence: list[dict],
) -> bool:
    """
    Require a key strength to contain meaningful terminology
    supported by at least one candidate-evidence item.

    A strength does not need to exactly match evidence wording,
    because reasonable paraphrasing is allowed.
    """

    strength_tokens = _meaningful_tokens(strength)

    if not strength_tokens:
        return False

    for item in candidate_evidence:
        evidence_text = normalize_text(
            f"{item.get('title', '')} "
            f"{item.get('content', '')}"
        )

        evidence_tokens = _meaningful_tokens(
            evidence_text
        )

        if not evidence_tokens:
            continue

        overlap = strength_tokens & evidence_tokens

        # Require at least two meaningful overlapping terms
        # unless the strength contains a highly specific
        # technical term.
        specific_terms = {
            token
            for token in overlap
            if any(
                character in token
                for character in ["+", "#", "."]
            )
            or token in {
                "python",
                "fastapi",
                "postgresql",
                "sql",
                "mongodb",
                "docker",
                "react",
                "django",
                "javascript",
                "typescript",
                "langchain",
                "streamlit",
                "tavily",
                "groq",
            }
        }

        if len(overlap) >= 2 or specific_terms:
            return True

    return False


def _validate_answer_against_used_evidence(
    answer: str,
    used_evidence: list[str],
    candidate_evidence: list[dict],
) -> list[str]:
    """
    Check that an answer has meaningful overlap with the specific
    evidence titles Gemini claimed to use.
    """

    unsupported = []

    evidence_by_title = _build_evidence_by_title(
        candidate_evidence
    )

    selected_records = []

    for title in used_evidence:
        normalized_title = normalize_text(title)

        record = evidence_by_title.get(
            normalized_title
        )

        if record is not None:
            selected_records.append(record)

    if not selected_records:
        return [
            "application answer has no valid supporting evidence"
        ]

    answer_tokens = _meaningful_tokens(answer)

    if not answer_tokens:
        return [
            "application answer contains no meaningful evidence-linked terms"
        ]

    selected_text = normalize_text(
        " ".join(
            f"{item.get('title', '')} "
            f"{item.get('content', '')}"
            for item in selected_records
        )
    )

    selected_tokens = _meaningful_tokens(
        selected_text
    )

    overlap = answer_tokens & selected_tokens

    if len(overlap) == 0:
        unsupported.append(
            "application answer is not supported by its declared evidence"
        )

    return unsupported


def validate_generated_summary(
    summary: str,
    candidate_evidence: list[dict],
    missing_requirements: list[str] | None = None,
) -> dict:
    """
    Validate generated resume/application text against verified
    candidate evidence and missing job requirements.
    """

    missing_requirements = (
        missing_requirements or []
    )

    unsupported_claims = []

    unsupported_claims.extend(
        _validate_text_against_evidence(
            text=summary,
            candidate_evidence=candidate_evidence,
        )
    )

    unsupported_claims.extend(
        _find_missing_requirement_claims(
            text=summary,
            missing_requirements=missing_requirements,
        )
    )

    return {
        "is_valid": len(unsupported_claims) == 0,
        "unsupported_claims": list(
            dict.fromkeys(unsupported_claims)
        ),
    }


def validate_application_package(
    package: dict,
    candidate_evidence: list[dict],
    missing_requirements: list[str] | None = None,
) -> dict:
    """
    Validate the complete generated application package.

    This is the deterministic trust gate before an application
    package is persisted.
    """

    missing_requirements = (
        missing_requirements or []
    )

    unsupported_claims = []

    evidence_ids = {
        str(item.get("evidence_id"))
        for item in candidate_evidence
        if item.get("evidence_id") is not None
    }

    evidence_titles = _build_evidence_titles(
        candidate_evidence
    )

    # ---------------------------------------------------------
    # 1. Structural validation
    # ---------------------------------------------------------

    required_fields = {
        "cover_letter",
        "key_strengths",
        "application_questions",
    }

    for field in required_fields:
        if field not in package:
            unsupported_claims.append(
                f"missing generated field: {field}"
            )

    if unsupported_claims:
        return {
            "is_valid": False,
            "unsupported_claims": unsupported_claims,
        }

    if not isinstance(
        package["cover_letter"],
        str,
    ):
        unsupported_claims.append(
            "cover_letter must be a string"
        )

    if not isinstance(
        package["key_strengths"],
        list,
    ):
        unsupported_claims.append(
            "key_strengths must be a list"
        )

    if not isinstance(
        package["application_questions"],
        list,
    ):
        unsupported_claims.append(
            "application_questions must be a list"
        )

    if unsupported_claims:
        return {
            "is_valid": False,
            "unsupported_claims": list(
                dict.fromkeys(unsupported_claims)
            ),
        }

    # ---------------------------------------------------------
    # 2. Cover letter validation
    # ---------------------------------------------------------

    cover_letter = package.get(
        "cover_letter",
        "",
    )

    if not cover_letter.strip():
        unsupported_claims.append(
            "empty cover letter"
        )

    unsupported_claims.extend(
        _validate_text_against_evidence(
            text=cover_letter,
            candidate_evidence=candidate_evidence,
        )
    )

    unsupported_claims.extend(
        _find_missing_requirement_claims(
            text=cover_letter,
            missing_requirements=missing_requirements,
        )
    )

    # ---------------------------------------------------------
    # 3. Key strengths validation
    # ---------------------------------------------------------

    strengths = package.get(
        "key_strengths",
        [],
    )

    if len(strengths) < 3:
        unsupported_claims.append(
            "fewer than 3 key strengths"
        )

    if len(strengths) > 5:
        unsupported_claims.append(
            "more than 5 key strengths"
        )

    for strength in strengths:

        if not isinstance(strength, str):
            unsupported_claims.append(
                "invalid key strength format"
            )
            continue

        if not strength.strip():
            unsupported_claims.append(
                "empty key strength"
            )
            continue

        if not _validate_strength(
            strength=strength,
            candidate_evidence=candidate_evidence,
        ):
            unsupported_claims.append(
                f"unsupported key strength: {strength}"
            )

    # ---------------------------------------------------------
    # 4. Application question validation
    # ---------------------------------------------------------

    questions = package.get(
        "application_questions",
        [],
    )

    if len(questions) != 3:
        unsupported_claims.append(
            "application package must contain exactly 3 questions"
        )

    for index, item in enumerate(questions):

        if not isinstance(item, dict):
            unsupported_claims.append(
                f"invalid application question at index {index}"
            )
            continue

        question = item.get(
            "question",
            "",
        )

        answer = item.get(
            "answer",
            "",
        )

        used_evidence = item.get(
            "evidence_used",
            [],
        )

        if not isinstance(question, str) or not question.strip():
            unsupported_claims.append(
                f"empty application question at index {index}"
            )

        if not isinstance(answer, str) or not answer.strip():
            unsupported_claims.append(
                f"empty application answer at index {index}"
            )

        if not isinstance(
            used_evidence,
            list,
        ):
            unsupported_claims.append(
                f"invalid evidence_used at index {index}"
            )
            continue

        if not used_evidence:
            unsupported_claims.append(
                f"application question has no evidence at index {index}"
            )
            continue

        valid_used_evidence = []

        for title in used_evidence:

            if not isinstance(title, str):
                unsupported_claims.append(
                    f"invalid evidence title at index {index}"
                )
                continue

            normalized_title = normalize_text(title)

            if normalized_title not in evidence_titles:
                unsupported_claims.append(
                    "application question references "
                    f"unknown evidence: {title}"
                )
            else:
                valid_used_evidence.append(title)

        unsupported_claims.extend(
            _validate_answer_against_used_evidence(
                answer=answer,
                used_evidence=valid_used_evidence,
                candidate_evidence=candidate_evidence,
            )
        )

        unsupported_claims.extend(
            _validate_text_against_evidence(
                text=answer,
                candidate_evidence=candidate_evidence,
            )
        )

        unsupported_claims.extend(
            _find_missing_requirement_claims(
                text=answer,
                missing_requirements=missing_requirements,
            )
        )

    # ---------------------------------------------------------
    # 5. Package evidence validation
    # ---------------------------------------------------------

    package_evidence = package.get(
        "evidence_used",
        [],
    )

    if isinstance(package_evidence, list):

        for evidence in package_evidence:

            if str(evidence) in evidence_ids:
                continue

            if (
                normalize_text(str(evidence))
                not in evidence_titles
            ):
                unsupported_claims.append(
                    "package references unknown evidence: "
                    f"{evidence}"
                )

    return {
        "is_valid": len(unsupported_claims) == 0,
        "unsupported_claims": list(
            dict.fromkeys(unsupported_claims)
        ),
    }