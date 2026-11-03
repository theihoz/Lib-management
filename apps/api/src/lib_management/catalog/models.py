"""Normalized catalog records; availability is derived from copies."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from lib_management.models import Base, created_at, uuid_pk


class Publisher(Base):
    __tablename__ = "publisher"
    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="name"),
        CheckConstraint("status IN ('ACTIVE','INACTIVE')", name="status"),
    )
    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(200))
    address: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = created_at()


class Author(Base):
    __tablename__ = "author"
    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="name"),
        CheckConstraint("status IN ('ACTIVE','INACTIVE')", name="status"),
    )
    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(200))
    biography: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = created_at()


class Category(Base):
    __tablename__ = "category"
    id: Mapped[uuid.UUID] = uuid_pk()
    code: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    parent_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("category.id"))
    is_root: Mapped[bool] = mapped_column(Boolean, server_default="false")
    created_at: Mapped[datetime] = created_at()


class BookEdition(Base):
    __tablename__ = "book_edition"
    __table_args__ = (
        CheckConstraint("length(trim(title)) > 0", name="title"),
        CheckConstraint("status IN ('ACTIVE','INACTIVE')", name="status"),
        CheckConstraint("version > 0", name="version"),
    )
    id: Mapped[uuid.UUID] = uuid_pk()
    isbn: Mapped[str | None] = mapped_column(String(13), unique=True)
    title: Mapped[str] = mapped_column(String(300))
    publication_year: Mapped[int] = mapped_column(SmallInteger)
    publisher_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("publisher.id"))
    language: Mapped[str | None] = mapped_column(String(32))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16))
    version: Mapped[int] = mapped_column(Integer, server_default="1")
    created_at: Mapped[datetime] = created_at()


class BookAuthor(Base):
    __tablename__ = "book_author"
    __table_args__ = (
        UniqueConstraint("edition_id", "ordinal"),
        CheckConstraint("ordinal > 0", name="ordinal"),
    )
    edition_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("book_edition.id"), primary_key=True
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("author.id"), primary_key=True
    )
    ordinal: Mapped[int] = mapped_column(SmallInteger)
    created_at: Mapped[datetime] = created_at()


class BookCategory(Base):
    __tablename__ = "book_category"
    edition_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("book_edition.id"), primary_key=True
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("category.id"), primary_key=True
    )
    created_at: Mapped[datetime] = created_at()


class Location(Base):
    __tablename__ = "location"
    __table_args__ = (
        CheckConstraint("status IN ('ACTIVE','INACTIVE')", name="status"),
    )
    id: Mapped[uuid.UUID] = uuid_pk()
    code: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = created_at()


class BookCopy(Base):
    __tablename__ = "book_copy"
    __table_args__ = (
        CheckConstraint(
            "status IN ('AVAILABLE','ON_LOAN','HELD','REPAIR','LOST','RETIRED')",
            name="status",
        ),
        CheckConstraint("version > 0", name="version"),
    )
    id: Mapped[uuid.UUID] = uuid_pk()
    edition_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("book_edition.id"), index=True
    )
    barcode: Mapped[str] = mapped_column(String(64), unique=True)
    location_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("location.id"))
    status: Mapped[str] = mapped_column(String(16))
    acquired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source_receipt_item_id: Mapped[uuid.UUID | None] = mapped_column()
    version: Mapped[int] = mapped_column(Integer, server_default="1")
    created_at: Mapped[datetime] = created_at()
