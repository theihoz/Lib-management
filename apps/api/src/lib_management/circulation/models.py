"""Normalized circulation and append-only ledger tables."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    Sequence,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column

from lib_management.models import Base, created_at, uuid_pk


class PolicyVersion(Base):
    __tablename__ = "policy_version"
    __table_args__ = (
        CheckConstraint("version_no > 0", name="version_no_positive"),
        CheckConstraint("status IN ('DRAFT', 'ACTIVE', 'SUPERSEDED')", name="status"),
        ExcludeConstraint(
            (text("tstzrange(effective_from, effective_to, '[)')"), "&&"),
            where=text("status IN ('ACTIVE', 'SUPERSEDED')"),
            using="gist",
            name="ex_policy_effective_range",
        ),
        Index("ix_policy_version_created_id", "created_at", "id"),
        CheckConstraint(
            "effective_to IS NULL OR effective_to > effective_from",
            name="effective_interval",
        ),
        CheckConstraint(
            (
                "(status = 'DRAFT' AND approved_by IS NULL AND approved_at IS NULL) "
                "OR (status IN ('ACTIVE','SUPERSEDED') AND approved_by IS NOT NULL "
                "AND approved_at IS NOT NULL)"
            ),
            name="approval_state",
        ),
    )
    id: Mapped[uuid.UUID] = uuid_pk()
    version_no: Mapped[int] = mapped_column(
        Integer, Sequence("policy_version_no_seq"), nullable=False, unique=True
    )
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    effective_to: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    rules: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    rules_schema_version: Mapped[int] = mapped_column(Integer, nullable=False)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("account.id"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = created_at()


class Loan(Base):
    __tablename__ = "loan"
    __table_args__ = (
        CheckConstraint("version > 0", name="version_positive"),
        Index("ix_loan_created_id", "created_at", "id"),
        CheckConstraint("renewal_count >= 0", name="renewal_count"),
    )
    id: Mapped[uuid.UUID] = uuid_pk()
    loan_no: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    reader_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reader.id"), nullable=False, index=True
    )
    card_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reader_card.id"), nullable=False
    )
    issued_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("account.id"), nullable=False
    )
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    renewal_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    created_at: Mapped[datetime] = created_at()


class LoanItem(Base):
    __tablename__ = "loan_item"
    __table_args__ = (
        CheckConstraint("version > 0", name="version_positive"),
        Index(
            "uq_loan_item_open_copy",
            "copy_id",
            unique=True,
            postgresql_where=text("closed_at IS NULL"),
        ),
        Index(
            "ix_loan_item_due_open",
            "due_at",
            "id",
            postgresql_where=text("closed_at IS NULL"),
        ),
        Index("ix_loan_item_created_id", "created_at", "id"),
        CheckConstraint("due_at > issued_at", name="due_after_issue"),
        CheckConstraint(
            (
                "(closed_at IS NULL AND closure_reason IS NULL) OR (closed_at IS NOT "
                "NULL AND closure_reason IN ('RETURNED','LOST','VOIDED'))"
            ),
            name="closure_state",
        ),
    )
    id: Mapped[uuid.UUID] = uuid_pk()
    loan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("loan.id"), nullable=False, index=True
    )
    copy_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("book_copy.id"), nullable=False
    )
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    closure_reason: Mapped[str | None] = mapped_column(String(16), nullable=True)
    policy_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("policy_version.id"), nullable=False
    )
    applied_rules: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    created_at: Mapped[datetime] = created_at()


class RenewalEvent(Base):
    __tablename__ = "renewal_event"
    __table_args__ = (
        Index("ix_renewal_event_created_id", "created_at", "id"),
        UniqueConstraint("loan_id", "sequence_no"),
        CheckConstraint("sequence_no > 0", name="sequence_positive"),
    )
    id: Mapped[uuid.UUID] = uuid_pk()
    loan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("loan.id"), nullable=False, index=True
    )
    sequence_no: Mapped[int] = mapped_column(Integer, nullable=False)
    actor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("account.id"), nullable=False
    )
    renewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    policy_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("policy_version.id"), nullable=False
    )
    request_id: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = created_at()


class RenewalItem(Base):
    __tablename__ = "renewal_item"
    __table_args__ = (CheckConstraint("new_due_at > old_due_at", name="due_increases"),)
    renewal_event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("renewal_event.id"), primary_key=True, nullable=False
    )
    loan_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("loan_item.id"), primary_key=True, nullable=False, index=True
    )
    old_due_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    new_due_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    applied_rules: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = created_at()


class ReturnEvent(Base):
    __tablename__ = "return_event"
    __table_args__ = (
        Index("ix_return_event_created_id", "created_at", "id"),
        CheckConstraint(
            (
                "(return_kind = 'RETURNED' AND condition IS NOT NULL AND "
                "condition IN ('GOOD','DAMAGED')) OR "
                "(return_kind IN ('LOST','VOIDED') AND condition IS NULL)"
            ),
            name="kind_condition",
        ),
    )
    id: Mapped[uuid.UUID] = uuid_pk()
    loan_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("loan_item.id"), nullable=False, unique=True, index=True
    )
    return_kind: Mapped[str] = mapped_column(String(16), nullable=False)
    condition: Mapped[str | None] = mapped_column(String(16), nullable=True)
    returned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    processed_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("account.id"), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = created_at()


class Reservation(Base):
    __tablename__ = "reservation"
    __table_args__ = (
        CheckConstraint(
            "status IN ('QUEUED', 'READY', 'FULFILLED', 'CANCELLED', 'EXPIRED')",
            name="status",
        ),
        CheckConstraint("version > 0", name="version_positive"),
        Index(
            "uq_reservation_active_reader_edition",
            "reader_id",
            "edition_id",
            unique=True,
            postgresql_where=text("status IN ('QUEUED', 'READY')"),
        ),
        Index(
            "uq_reservation_ready_copy",
            "copy_id",
            unique=True,
            postgresql_where=text("status = 'READY'"),
        ),
        Index("ix_reservation_created_id", "created_at", "id"),
        CheckConstraint(
            (
                "status != 'READY' OR (copy_id IS NOT NULL AND ready_at IS NOT NULL "
                "AND ready_expires_at IS NOT NULL AND ready_expires_at > ready_at)"
            ),
            name="ready_state",
        ),
    )
    id: Mapped[uuid.UUID] = uuid_pk()
    reader_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reader.id"), nullable=False, index=True
    )
    edition_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("book_edition.id"), nullable=False, index=True
    )
    copy_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("book_copy.id"), nullable=True
    )
    fulfilled_loan_item_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("loan_item.id"), nullable=True, unique=True
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    ready_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ready_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    policy_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("policy_version.id"), nullable=False
    )
    applied_rules: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    created_at: Mapped[datetime] = created_at()


class FineCharge(Base):
    __tablename__ = "fine_charge"
    __table_args__ = (
        CheckConstraint("assessed_amount > 0", name="assessed_amount_positive"),
        Index("ix_fine_charge_created_id", "created_at", "id"),
        CheckConstraint("reason IN ('LATE','DAMAGE','LOST','MANUAL')", name="reason"),
        CheckConstraint("late_days IS NULL OR late_days >= 0", name="late_days"),
    )
    id: Mapped[uuid.UUID] = uuid_pk()
    reader_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reader.id"), nullable=False, index=True
    )
    loan_item_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("loan_item.id"), nullable=True, index=True
    )
    policy_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("policy_version.id"), nullable=False
    )
    reason: Mapped[str] = mapped_column(String(16), nullable=False)
    assessed_amount: Mapped[Decimal] = mapped_column(Numeric(14, 0), nullable=False)
    late_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    unit_rate: Mapped[Decimal | None] = mapped_column(Numeric(14, 0), nullable=True)
    calculation: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    manual_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    assessed_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("account.id"), nullable=False
    )
    created_at: Mapped[datetime] = created_at()


class Payment(Base):
    __tablename__ = "payment"
    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        Index("ix_payment_created_id", "created_at", "id"),
        CheckConstraint("method IN ('CASH','TRANSFER_RECORD')", name="method"),
    )
    id: Mapped[uuid.UUID] = uuid_pk()
    reader_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reader.id"), nullable=False, index=True
    )
    receipt_no: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 0), nullable=False)
    method: Mapped[str] = mapped_column(String(24), nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    received_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("account.id"), nullable=False
    )
    reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = created_at()


class PaymentAllocation(Base):
    __tablename__ = "payment_allocation"
    __table_args__ = (CheckConstraint("amount > 0", name="amount_positive"),)
    payment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("payment.id"), primary_key=True, nullable=False, index=True
    )
    charge_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fine_charge.id"), primary_key=True, nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 0), nullable=False)
    created_at: Mapped[datetime] = created_at()


class Waiver(Base):
    __tablename__ = "waiver"
    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        Index("ix_waiver_created_id", "created_at", "id"),
        CheckConstraint("length(trim(reason)) > 0", name="reason"),
    )
    id: Mapped[uuid.UUID] = uuid_pk()
    charge_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fine_charge.id"), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 0), nullable=False)
    approved_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("account.id"), nullable=False
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = created_at()


class PaymentReversal(Base):
    __tablename__ = "payment_reversal"
    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        Index("ix_payment_reversal_created_id", "created_at", "id"),
    )
    id: Mapped[uuid.UUID] = uuid_pk()
    payment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("payment.id"), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 0), nullable=False)
    actor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("account.id"), nullable=False
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = created_at()


class AllocationReversal(Base):
    __tablename__ = "allocation_reversal"
    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        ForeignKeyConstraint(
            ["payment_id", "charge_id"],
            ["payment_allocation.payment_id", "payment_allocation.charge_id"],
        ),
        Index("ix_allocation_reversal_created_id", "created_at", "id"),
    )
    id: Mapped[uuid.UUID] = uuid_pk()
    payment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("payment.id"), nullable=False, index=True
    )
    charge_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fine_charge.id"), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 0), nullable=False)
    actor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("account.id"), nullable=False
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = created_at()


class WaiverReversal(Base):
    __tablename__ = "waiver_reversal"
    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        Index("ix_waiver_reversal_created_id", "created_at", "id"),
    )
    id: Mapped[uuid.UUID] = uuid_pk()
    waiver_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("waiver.id"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 0), nullable=False)
    actor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("account.id"), nullable=False
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = created_at()


class ChargeAssessment(Base):
    __tablename__ = "charge_assessment"
    __table_args__ = (
        UniqueConstraint("return_event_id", "kind"),
        CheckConstraint("kind IN ('DAMAGE','LOST','MANUAL')", name="kind"),
        # YC#11 / D2: a manual fine is not tied to a return.
        CheckConstraint(
            "(kind = 'MANUAL') = (return_event_id IS NULL)", name="manual_source"
        ),
        CheckConstraint(
            "status IN ('PENDING','ASSESSED','CLOSED_NO_CHARGE')", name="status"
        ),
        CheckConstraint("proposed_amount >= 0", name="proposed_amount"),
        CheckConstraint("version > 0", name="version_positive"),
        CheckConstraint(
            (
                "(status = 'PENDING' AND approved_amount IS NULL AND decided_by IS "
                "NULL AND decided_at IS NULL AND decision_reason IS NULL AND "
                "fine_charge_id IS NULL) OR (status = 'ASSESSED' AND approved_amount "
                "> 0 AND decided_by IS NOT NULL AND decided_at IS NOT NULL AND "
                "decision_reason IS NOT NULL AND "
                "length(trim(decision_reason)) > 0 AND "
                "fine_charge_id IS NOT NULL) OR"
                " (status = 'CLOSED_NO_CHARGE' AND approved_amount = 0 AND decided_by"
                " IS NOT NULL AND decided_at IS NOT NULL AND "
                "decision_reason IS NOT NULL AND "
                "length(trim(decision_reason)) > 0 AND fine_charge_id IS NULL)"
            ),
            name="decision_state",
        ),
        Index("ix_charge_assessment_reader_status", "reader_id", "status"),
    )
    id: Mapped[uuid.UUID] = uuid_pk()
    reader_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reader.id"), nullable=False
    )
    return_event_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("return_event.id"), nullable=True
    )
    loan_item_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("loan_item.id"), nullable=True
    )
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    proposed_amount: Mapped[Decimal] = mapped_column(Numeric(14, 0), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    proposed_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("account.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    approved_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 0))
    decided_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("account.id"))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decision_reason: Mapped[str | None] = mapped_column(Text)
    fine_charge_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("fine_charge.id"), unique=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    created_at: Mapped[datetime] = created_at()
