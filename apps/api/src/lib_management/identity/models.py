"""Identity tables (database-design.md §12–16)."""

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from lib_management.models import Base, created_at, uuid_pk

ACCOUNT_STATUSES = ("ACTIVE", "LOCKED", "DISABLED")


class Account(Base):
    __tablename__ = "account"
    __table_args__ = (
        UniqueConstraint("issuer", "subject"),
        CheckConstraint("status IN ('ACTIVE', 'LOCKED', 'DISABLED')", name="status"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    issuer: Mapped[str] = mapped_column(Text, nullable=False)
    subject: Mapped[str] = mapped_column(Text, nullable=False)
    reader_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("reader.id"), unique=True
    )
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    auth_version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="1"
    )
    created_at: Mapped[datetime] = created_at()


class Role(Base):
    __tablename__ = "role"

    id: Mapped[uuid.UUID] = uuid_pk()
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = created_at()


class Permission(Base):
    __tablename__ = "permission"

    id: Mapped[uuid.UUID] = uuid_pk()
    code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = created_at()


class AccountRole(Base):
    __tablename__ = "account_role"

    account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("account.id"), primary_key=True
    )
    role_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("role.id"), primary_key=True)
    granted_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("account.id"), nullable=False
    )
    created_at: Mapped[datetime] = created_at()


class RolePermission(Base):
    __tablename__ = "role_permission"

    role_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("role.id"), primary_key=True)
    permission_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("permission.id"), primary_key=True
    )
    created_at: Mapped[datetime] = created_at()
