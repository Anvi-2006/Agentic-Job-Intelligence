import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
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

    requirement: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    requirement_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    importance: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "job_id",
            "requirement",
            name="uq_job_requirement_job_requirement",
        ),
    )