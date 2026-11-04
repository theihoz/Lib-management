"""Acquisition receipts (database-design.md §36–37, F22, phase 2)."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from lib_management.models import Base, created_at, uuid_pk


class AcquisitionReceipt(Base):
    """POSTED is immutable; the receipt total is derived from its items."""

    __tablename__ = "acquisition_receipt"
    __table_args__ = (
        CheckConstraint("status IN ('DRAFT','POSTED','CANCELLED')", name="status"),
        CheckConstraint(
            "status <> 'POSTED' OR approved_by IS NOT NULL", name="posted_approved"
        ),
    )
    id: Mapped[uuid.UUID] = uuid_pk()
    receipt_no: Mapped[str] = mapped_column(String(64), unique=True)
    supplier: Mapped[str] = mapped_column(String(200))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(16))
    approved_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("account.id"))
    created_at: Mapped[datetime] = created_at()


class AcquisitionReceiptItem(Base):
    __tablename__ = "acquisition_receipt_item"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint("unit_price >= 0", name="unit_price_non_negative"),
    )
    id: Mapped[uuid.UUID] = uuid_pk()
    receipt_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("acquisition_receipt.id"), index=True
    )
    edition_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("book_edition.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 0))
    created_at: Mapped[datetime] = created_at()
