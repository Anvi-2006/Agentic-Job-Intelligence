import uuid

from sqlalchemy import DateTime, Float, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from backend.app.core.database import Base


class ApplicationPackage(Base):
    __tablename__ = "application_packages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    readiness_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    tailored_summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    cover_letter: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    key_strengths: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
    )

    missing_requirements: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
    )

    application_questions: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
    )

    evidence_used: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
    )

    unsupported_claims: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
    )

    is_valid: Mapped[bool] = mapped_column(
        nullable=False,
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    