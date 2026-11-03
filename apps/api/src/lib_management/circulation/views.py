"""Typed REST entity projections from the approved API contract."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class View(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class PolicyVersion(View):
    id: UUID
    version_no: int
    effective_from: datetime
    effective_to: datetime | None = Field(default=None)
    status: str = Field(max_length=16)
    rules: dict[str, Any]
    rules_schema_version: int
    approved_by: UUID | None = Field(default=None)
    approved_at: datetime | None = Field(default=None)
    created_at: datetime


class Loan(View):
    id: UUID
    loan_no: str = Field(max_length=64)
    reader_id: UUID
    card_id: UUID
    issued_by: UUID
    issued_at: datetime
    renewal_count: int
    version: int
    created_at: datetime


class LoanItem(View):
    id: UUID
    loan_id: UUID
    copy_id: UUID
    issued_at: datetime
    due_at: datetime
    closed_at: datetime | None = Field(default=None)
    closure_reason: str | None = Field(default=None, max_length=16)
    policy_version_id: UUID
    applied_rules: dict[str, Any]
    version: int
    created_at: datetime


class RenewalEvent(View):
    id: UUID
    loan_id: UUID
    sequence_no: int
    actor_id: UUID
    renewed_at: datetime
    policy_version_id: UUID
    request_id: str = Field(max_length=100)
    created_at: datetime


class ReturnEvent(View):
    id: UUID
    loan_item_id: UUID
    return_kind: str = Field(max_length=16)
    condition: str | None = Field(default=None, max_length=16)
    returned_at: datetime
    processed_by: UUID
    notes: str | None = Field(default=None)
    created_at: datetime


class FineCharge(View):
    id: UUID
    reader_id: UUID
    loan_item_id: UUID | None = Field(default=None)
    policy_version_id: UUID
    reason: str = Field(max_length=16)
    assessed_amount: str = Field(pattern="^[0-9]+$")
    late_days: int | None = Field(default=None)
    unit_rate: str | None = Field(default=None, pattern="^[0-9]+$")
    calculation: dict[str, Any]
    manual_reason: str | None = Field(default=None)
    assessed_by: UUID
    created_at: datetime


class ReturnReceipt(View):
    returnEvent: ReturnEvent
    copyStatus: str = Field(min_length=1)
    charges: list[FineCharge]
    assessmentId: UUID | None = Field(default=None)


class CheckoutReceiptItemsItem(View):
    loanItemId: UUID
    copyId: UUID
    dueAt: datetime


class CheckoutReceipt(View):
    loanId: UUID
    items: list[CheckoutReceiptItemsItem]
    policyVersionId: UUID
    requestId: str = Field(min_length=1)


class ChargeAssessment(View):
    id: UUID
    reader_id: UUID
    return_event_id: UUID
    kind: Literal["DAMAGE", "LOST"]
    status: Literal["PENDING", "ASSESSED", "CLOSED_NO_CHARGE"]
    proposed_amount: str = Field(pattern="^[0-9]+$")
    approved_amount: str | None = Field(default=None, pattern="^[0-9]+$")
    reason: str = Field(min_length=1)
    version: int = Field(ge=1)


class Payment(View):
    id: UUID
    reader_id: UUID
    receipt_no: str = Field(max_length=64)
    amount: str = Field(pattern="^[0-9]+$")
    method: str = Field(max_length=24)
    received_at: datetime
    received_by: UUID
    reference: str | None = Field(default=None)
    created_at: datetime


class Waiver(View):
    id: UUID
    charge_id: UUID
    amount: str = Field(pattern="^[0-9]+$")
    approved_by: UUID
    reason: str
    created_at: datetime


class LedgerReversalReceipt(View):
    reversalType: Literal["PAYMENT", "ALLOCATION", "WAIVER"]
    reversalId: UUID
    requestId: str | None = Field(default=None)


class Reservation(View):
    id: UUID
    reader_id: UUID
    edition_id: UUID
    copy_id: UUID | None = Field(default=None)
    fulfilled_loan_item_id: UUID | None = Field(default=None)
    status: str = Field(max_length=16)
    ready_at: datetime | None = Field(default=None)
    ready_expires_at: datetime | None = Field(default=None)
    cancellation_reason: str | None = Field(default=None)
    policy_version_id: UUID
    applied_rules: dict[str, Any]
    version: int
    created_at: datetime


class BookCopy(View):
    id: UUID
    edition_id: UUID
    barcode: str = Field(max_length=64)
    location_id: UUID | None = Field(default=None)
    status: str = Field(max_length=16)
    acquired_at: datetime
    source_receipt_item_id: UUID | None = Field(default=None)
    version: int
    created_at: datetime


class BookEdition(View):
    id: UUID
    isbn: str | None = Field(default=None, max_length=13)
    title: str = Field(max_length=300)
    publication_year: int
    publisher_id: UUID | None = Field(default=None)
    language: str | None = Field(default=None, max_length=32)
    description: str | None = Field(default=None)
    status: str = Field(max_length=16)
    version: int
    created_at: datetime


class Location(View):
    id: UUID
    code: str = Field(max_length=32)
    name: str = Field(max_length=120)
    status: str = Field(max_length=16)
    created_at: datetime
