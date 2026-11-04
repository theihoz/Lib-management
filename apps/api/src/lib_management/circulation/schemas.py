"""Validated write DTOs mirroring the approved REST contract."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

# QĐ07: a lost book costs 100.000–600.000 VND depending on the book.
LOST_FEE_MIN = Decimal(100_000)
LOST_FEE_MAX = Decimal(600_000)
# Hard upper bound for one loan; the active policy (QĐ05) sets the real limit.
MAX_COPIES_PER_REQUEST = 20

Money = Annotated[str, Field(pattern="^[0-9]+$", max_length=12)]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class DamageLostFees(Input):
    """BM09 fee frame; the amount a Librarian proposes by default."""

    MINOR_DAMAGE: Money
    MAJOR_DAMAGE: Money
    LOST: Money


class PolicyRules(Input):
    """rulesSchemaVersion 2: QĐ01–QĐ08 values plus the BM09 configuration (QĐ17)."""

    libraryName: str = Field(min_length=1, max_length=200)
    minReaderAge: int = Field(ge=1, le=120)
    maxReaderAge: int = Field(ge=1, le=120)
    cardValidityMonths: int = Field(ge=1, le=120)
    maxBooksPerLoan: int = Field(ge=1, le=MAX_COPIES_PER_REQUEST)
    initialLoanDays: int = Field(ge=1, le=365)
    maxRenewals: int = Field(ge=0, le=10)
    renewalDays: int = Field(ge=1, le=365)
    overdueFinePerDay: Money
    allowedOutstandingBalance: Money
    publicationYearWindow: int = Field(ge=0, le=200)
    readyHoldDays: int = Field(ge=1, le=60)
    damageLostAssessment: Literal["MANUAL_APPROVAL"]
    damageLostFees: DamageLostFees

    @model_validator(mode="after")
    def check(self) -> Self:
        if self.minReaderAge > self.maxReaderAge:
            raise ValueError("minReaderAge must not exceed maxReaderAge")
        if Decimal(self.allowedOutstandingBalance) <= 0:
            raise ValueError("allowedOutstandingBalance must be greater than 0")
        if not LOST_FEE_MIN <= Decimal(self.damageLostFees.LOST) <= LOST_FEE_MAX:
            raise ValueError("damageLostFees.LOST must be within 100000-600000")
        return self


class CheckoutRequest(Input):
    readerId: UUID
    copyIds: list[UUID] = Field(min_length=1, max_length=MAX_COPIES_PER_REQUEST)


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


class CopyStatusRequest(Input):
    expectedVersion: int = Field(ge=1)
    status: Literal["AVAILABLE", "REPAIR", "MAINTENANCE", "LOST"]
    reason: str | None = Field(default=None, max_length=500)


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
    rulesSchemaVersion: Literal[2]
    rules: PolicyRules


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
