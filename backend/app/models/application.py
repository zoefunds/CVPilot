"""
Application + FileAsset ORM models.
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin

# Postgres ENUM types are created once and reused.
application_status_enum = ENUM(
    "pending",
    "processing",
    "ready",
    "evaluating",
    "complete",
    "failed",
    name="application_status",
    create_type=True,
)

file_kind_enum = ENUM(
    "cv",
    "cover_letter",
    name="file_kind",
    create_type=True,
)


class Application(Base, TimestampMixin):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    job_final_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    job_title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    job_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    portfolio_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    status: Mapped[str] = mapped_column(application_status_enum, default="pending", nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    files: Mapped[list[FileAsset]] = relationship(
        "FileAsset",
        back_populates="application",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class FileAsset(Base, TimestampMixin):
    __tablename__ = "file_assets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    kind: Mapped[str] = mapped_column(file_kind_enum, nullable=False)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False)
    detected_kind: Mapped[str | None] = mapped_column(String(16), nullable=True)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    application: Mapped[Application] = relationship("Application", back_populates="files")
