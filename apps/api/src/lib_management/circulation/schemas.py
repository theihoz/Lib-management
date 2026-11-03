"""Validated write DTOs mirroring the approved REST contract."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CheckoutRequest(Input):
    readerId: UUID
    copyIds: list[UUID] = Field(min_length=1, max_length=4)


class AssessmentProposal(Input):
    proposedAmount: str = Field(pattern="^[0-9]+$")
    reason: str = Field(min_length=1)


class ReturnRequest(Input):
    loanItemId: UUID
    condition: Literal["GOOD", "DAMAGE", "LOST"]
    notes: str | None = Field(default=None)
    assessment: AssessmentProposal | None = Field(default=None)


class RenewRequest(Input):
    expectedVersion: int = Field(ge=1)


class HoldRequest(Input):
    editionId: UUID
    readerId: UUID | None = Field(default=None)


class ReasonRequest(Input):
    reason: str = Field(min_length=1)
    expectedVersion: int | None = Field(default=None, ge=1)


class DecisionRequest(Input):
    expectedVersion: int = Field(ge=1)
    amount: str = Field(pattern="^[0-9]+$")
    reason: str = Field(min_length=1)


class WaiverRequest(Input):
    amount: str = Field(pattern="^[0-9]+$")
    reason: str = Field(min_length=1)


class ReversalRequest(Input):
    entryType: Literal["PAYMENT", "ALLOCATION", "WAIVER"]
    entryId: UUID
    chargeId: UUID | None = Field(default=None)
    amount: str = Field(pattern="^[0-9]+$")
    reason: str = Field(min_length=1)


class VersionRequest(Input):
    expectedVersion: int = Field(ge=1)


class PolicyRequest(Input):
    effectiveFrom: datetime
    rulesSchemaVersion: int = Field(ge=1)
    rules: dict[str, Any]


class PaymentRequestAllocationsItem(Input):
    chargeId: UUID
    amount: str = Field(pattern="^[0-9]+$")


class PaymentRequest(Input):
    readerId: UUID
    amount: str = Field(pattern="^[0-9]+$")
    method: Literal["CASH", "TRANSFER_RECORD"]
    reference: str | None = Field(default=None)
    allocations: list[PaymentRequestAllocationsItem] = Field(min_length=1)


class ReportRequest(Input):
    reportType: str = Field(min_length=1)
    filters: dict[str, Any]
    asOf: datetime | None = Field(default=None)


class UploadRequest(Input):
    editionId: UUID
    mimeType: Literal["image/jpeg", "image/png", "image/webp"]
    byteSize: int = Field(ge=1)
    sha256: str = Field(pattern="^[0-9a-f]{64}$")


class ProvisionRequest(Input):
    readerId: UUID
    email: str


class AccountPatch(Input):
    status: Literal["ACTIVE", "DISABLED"]


class RoleRequest(Input):
    code: str = Field(min_length=1)
    name: str = Field(min_length=1)


class RoleAssignment(Input):
    roleIds: list[UUID]


class PermissionAssignment(Input):
    permissionIds: list[UUID]


class ReceiptRequestItemsItem(Input):
    editionId: UUID
    quantity: int = Field(ge=1)
    unitPrice: str = Field(pattern="^[0-9]+$")


class ReceiptRequest(Input):
    supplier: str = Field(min_length=1)
    receivedAt: datetime
    items: list[ReceiptRequestItemsItem] = Field(min_length=1)


class ReceiptPostItemsItem(Input):
    receiptItemId: UUID
    barcodes: list[str]
    locationId: UUID


class ReceiptPost(Input):
    items: list[ReceiptPostItemsItem]


class RestoreRequest(Input):
    manifestId: UUID
    targetAlias: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class BackupRequest(Input):
    targetAlias: str = Field(min_length=1)


class ConsentRequest(Input):
    emailConsent: bool
