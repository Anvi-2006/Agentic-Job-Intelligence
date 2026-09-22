import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, JSON, DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base


class SemanticMatchCache(Base):
    __tablename__ = "semantic_match_cache"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("candidate_profiles.id"),
        nullable=False,
    )

    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("jobs.id"),
        nullable=False,
    )

    results: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
    )

    matcher_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="v1",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    __table_args__ = (
        UniqueConstraint(
            "candidate_id",
            "job_id",
            "matcher_version",
            name="uq_semantic_match_candidate_job_version",
        ),
    )