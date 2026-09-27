import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

from types import SimpleNamespace

from backend.app.services.job_matching_service import (
    _exact_match,
    _related_competency_match,
)


def _requirement(name):
    return SimpleNamespace(
        requirement=name,
        normalized_name=name.lower(),
        original_text=name,
        context=name,
    )


def _evidence(title="", content=""):
    return SimpleNamespace(
        title=title,
        content=content,
    )


def test_exact_match_matches_same_skill():
    requirement = _requirement("Python")
    evidence = _evidence(
        title="Python",
        content="Built backend services using Python.",
    )

    assert _exact_match(requirement, evidence) is True


def test_exact_match_does_not_match_java_inside_javascript():
    requirement = _requirement("Java")
    evidence = _evidence(
        title="JavaScript Developer",
        content="Built frontend applications using JavaScript.",
    )

    assert _exact_match(requirement, evidence) is False


def test_exact_match_does_not_match_sql_inside_postgresql():
    requirement = _requirement("SQL")
    evidence = _evidence(
        title="PostgreSQL Developer",
        content="Built database systems using PostgreSQL.",
    )

    assert _exact_match(requirement, evidence) is False


def test_exact_match_matches_skill_in_evidence_content():
    requirement = _requirement("FastAPI")
    evidence = _evidence(
        title="Backend Engineer",
        content="Developed REST APIs using FastAPI and PostgreSQL.",
    )

    assert _exact_match(requirement, evidence) is True


def test_related_competency_returns_match():
    requirement = _requirement("REST APIs")
    evidence = _evidence(
        title="Backend Development",
        content="Built services using FastAPI.",
    )

    matched, competency = _related_competency_match(
        requirement,
        evidence,
    )

    assert matched is True
    assert competency == "fastapi"
