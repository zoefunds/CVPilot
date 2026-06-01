"""
Evaluation ORM. One Evaluation row per Application (latest-wins for now).
"""

from __future__ import annotations

import uuid

from sqlalchemy import JSON, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, TimestampMixin

evaluation_status_enum = ENUM(
    "pending",
    "running",
    "complete",
    "failed",
    name="evaluation_status",
    create_type=True,
)


class Evaluation(Base, TimestampMixin):
    __tablename__ = "evaluations"
    __table_args__ = (
        UniqueConstraint("application_id", name="uq_evaluations_application_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        evaluation_status_enum, default="pending", nullable=False
    )
    backend: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Score fields
    cv_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cover_letter_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    job_match_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ats_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    competitiveness_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    overall_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Narrative
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    improved_positioning: Mapped[str | None] = mapped_column(Text, nullable=True)

    # List fields
    recommendations: Mapped[list | None] = mapped_column(JSON, nullable=True)
    missing_keywords: Mapped[list | None] = mapped_column(JSON, nullable=True)
    missing_skills: Mapped[list | None] = mapped_column(JSON, nullable=True)
    weak_statements: Mapped[list | None] = mapped_column(JSON, nullable=True)
    company_alignment_notes: Mapped[list | None] = mapped_column(JSON, nullable=True)
    strengths: Mapped[list | None] = mapped_column(JSON, nullable=True)
    risks: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Per-score rationale (dict)
    rationale: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # On-chain provenance
    raw: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    contract_tx_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    contract_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
