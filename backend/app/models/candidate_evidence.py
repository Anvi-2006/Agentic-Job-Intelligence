import uuid

from sqlalchemy import ForeignKey, String, Text, Column
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base
from pgvector.sqlalchemy import Vector


class CandidateEvidence(Base):
    __tablename__ = "candidate_evidence"
    embedding = Column(
        Vector(1536),
        nullable=True
    )
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("candidate_profiles.id"),
        nullable=False,
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    
