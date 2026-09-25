import uuid

from sqlalchemy import Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base


class JobRequirement(Base):
    __tablename__ = "job_requirements"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("jobs.id"),
        nullable=False,
    )

    # Human-readable normalized requirement name.
    # Example: "Python", "FastAPI", "Machine Learning"
    requirement: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Canonical form used by matching.
    # Example: "python", "fastapi", "machine learning"
    normalized_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Original wording from the job description.
    original_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Context surrounding the requirement.
    # Example:
    # "Experience building backend services using Python"
    context: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # skill / experience / education / certification / domain / etc.
    requirement_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # technical / behavioral / domain / infrastructure / etc.
    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # required / preferred / nice_to_have
    importance: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # Confidence in the extraction/interpretation.
    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    # deterministic / llm / hybrid
    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="hybrid",
    )

    __table_args__ = (
        UniqueConstraint(
            "job_id",
            "normalized_name",
            name="uq_job_requirement_job_normalized_name",
        ),
    )