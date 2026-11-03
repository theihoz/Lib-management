"""Reader identities and immutable card issuance history."""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from lib_management.models import Base, created_at, uuid_pk


class Reader(Base):
    __tablename__ = "reader"
    __table_args__ = (
        CheckConstraint("status IN ('ACTIVE','SUSPENDED','INACTIVE')", name="status"),
        CheckConstraint("version > 0", name="version"),
    )
    id: Mapped[uuid.UUID] = uuid_pk()
    reader_code: Mapped[str] = mapped_column(String(32), unique=True)
    full_name: Mapped[str] = mapped_column(String(200))
    birth_date: Mapped[date] = mapped_column(Date)
    reader_type: Mapped[str] = mapped_column(String(8))
    email: Mapped[str | None] = mapped_column(String(254))
    phone: Mapped[str | None] = mapped_column(String(32))
    address: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16))
    version: Mapped[int] = mapped_column(Integer, server_default="1")
    created_at: Mapped[datetime] = created_at()


class ReaderCard(Base):
    __tablename__ = "reader_card"
    __table_args__ = (
        CheckConstraint("status IN ('ACTIVE','BLOCKED','REVOKED')", name="status"),
        CheckConstraint("expires_at > issued_at", name="validity"),
        CheckConstraint("version > 0", name="version"),
    )
    id: Mapped[uuid.UUID] = uuid_pk()
    reader_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("reader.id"), index=True)
    card_no: Mapped[str] = mapped_column(String(64), unique=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(16))
    issued_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("account.id"))
    policy_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("policy_version.id")
    )
    version: Mapped[int] = mapped_column(Integer, server_default="1")
    created_at: Mapped[datetime] = created_at()
