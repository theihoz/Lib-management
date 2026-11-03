"""Shared policy, eligibility and append-only ledger projections."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from lib_management.circulation.models import (
    AllocationReversal,
    ChargeAssessment,
    FineCharge,
    Loan,
    LoanItem,
    PaymentAllocation,
    PolicyVersion,
    Waiver,
    WaiverReversal,
)
from lib_management.core.errors import AppError, NotFound

RULES: dict[str, Any] = {
    "minReaderAge": 12,
    "maxReaderAge": 55,
    "cardValidityMonths": 6,
    "maxBooksPerLoan": 4,
    "initialLoanDays": 4,
    "maxRenewals": 1,
    "renewalDays": 4,
    "overdueFinePerDay": "1000",
    "allowedOutstandingBalance": "0",
    "publicationYearWindow": 8,
    "readyHoldDays": 3,
    "damageLostAssessment": "MANUAL_APPROVAL",
}


def active_policy(session: Session, now: datetime | None = None) -> PolicyVersion:
    now = now or datetime.now(UTC)
    policy = session.scalar(
        select(PolicyVersion).where(
            PolicyVersion.status.in_(["ACTIVE", "SUPERSEDED"]),
            PolicyVersion.effective_from <= now,
            (PolicyVersion.effective_to.is_(None) | (PolicyVersion.effective_to > now)),
        )
    )
    if policy is None:
        raise AppError(422, "POLICY_NOT_EFFECTIVE", "Chưa có quy định có hiệu lực")
    return policy


def view(row: Any) -> dict[str, Any]:
    """Return scalar entity columns; money is always an integer VND string."""
    return {
        column.key: (
            str(value) if isinstance(value, Decimal) else jsonable_encoder(value)
        )
        for column in row.__table__.columns
        for value in [getattr(row, column.key)]
    }


def total(session: Session, model: Any, condition: Any) -> Decimal:
    return Decimal(
        session.scalar(
            select(func.coalesce(func.sum(model.amount), 0)).where(condition)
        )
        or 0
    )


def charge_balance(session: Session, charge_id: UUID) -> Decimal:
    charge = session.get(FineCharge, charge_id)
    if charge is None:
        raise NotFound()
    paid = total(session, PaymentAllocation, PaymentAllocation.charge_id == charge_id)
    reversed_paid = total(
        session, AllocationReversal, AllocationReversal.charge_id == charge_id
    )
    waived = total(session, Waiver, Waiver.charge_id == charge_id)
    reversed_waived = Decimal(
        session.scalar(
            select(func.coalesce(func.sum(WaiverReversal.amount), 0))
            .join(Waiver, Waiver.id == WaiverReversal.waiver_id)
            .where(Waiver.charge_id == charge_id)
        )
        or 0
    )
    return charge.assessed_amount - paid + reversed_paid - waived + reversed_waived


def outstanding(session: Session, reader_id: UUID) -> Decimal:
    ids = session.scalars(
        select(FineCharge.id).where(FineCharge.reader_id == reader_id)
    )
    return sum((charge_balance(session, identifier) for identifier in ids), Decimal(0))


def eligibility(session: Session, reader_id: UUID) -> dict[str, Any]:
    from lib_management.readers.models import Reader, ReaderCard

    now = datetime.now(UTC)
    policy = active_policy(session, now)
    reader = session.get(Reader, reader_id)
    if reader is None:
        raise NotFound()
    reasons = []
    if reader.status != "ACTIVE":
        reasons.append("READER_INACTIVE")
    card = session.scalar(
        select(ReaderCard).where(
            ReaderCard.reader_id == reader_id,
            ReaderCard.status == "ACTIVE",
            ReaderCard.expires_at > now,
        )
    )
    if card is None:
        reasons.append("CARD_NOT_VALID")
    if outstanding(session, reader_id) > 0:
        reasons.append("OUTSTANDING_BALANCE")
    if session.scalar(
        select(LoanItem.id)
        .join(Loan, Loan.id == LoanItem.loan_id)
        .where(
            Loan.reader_id == reader_id,
            LoanItem.closed_at.is_(None),
            LoanItem.due_at < now,
        )
        .limit(1)
    ):
        reasons.append("OVERDUE_ITEMS")
    if session.scalar(
        select(ChargeAssessment.id)
        .where(
            ChargeAssessment.reader_id == reader_id,
            ChargeAssessment.status == "PENDING",
        )
        .limit(1)
    ):
        reasons.append("PENDING_ASSESSMENT")
    return {
        "allowed": not reasons,
        "reasons": reasons,
        "policyVersionId": str(policy.id),
        "evaluatedAt": now.isoformat(),
    }
