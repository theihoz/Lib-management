"""Normalized report metadata; artifact content lives behind private storage."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    CHAR,
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from lib_management.models import Base, created_at, uuid_pk


class MediaAsset(Base):
    __tablename__ = "media_asset"
    __table_args__ = (
        CheckConstraint("byte_size > 0", name="byte_size_positive"),
        CheckConstraint("visibility IN ('PUBLIC','PRIVATE')", name="visibility"),
        CheckConstraint(
            "status IN ('PENDING','READY','REJECTED','DELETED')", name="status"
        ),
    )
    id: Mapped[uuid.UUID] = uuid_pk()
    edition_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("book_edition.id"))
    object_key: Mapped[str] = mapped_column(Text, unique=True)
    mime_type: Mapped[str] = mapped_column(String(100))
    byte_size: Mapped[int] = mapped_column(BigInteger)
    sha256: Mapped[str] = mapped_column(CHAR(64))
    visibility: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16))
    uploaded_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("account.id"))
    created_at: Mapped[datetime] = created_at()


class ReportJob(Base):
    __tablename__ = "report_job"
    __table_args__ = (
        CheckConstraint("row_count >= 0", name="row_count_non_negative"),
        Index("ix_report_job_requested_by_created_at", "requested_by", "created_at"),
    )
    id: Mapped[uuid.UUID] = uuid_pk()
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("job.id"), unique=True)
    requested_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("account.id"))
    report_type: Mapped[str] = mapped_column(String(64))
    filter_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB)
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    artifact_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("media_asset.id"))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    row_count: Mapped[int | None] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = created_at()
