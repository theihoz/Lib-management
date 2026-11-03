"""Transactional circulation, policy and finance REST operations."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Header, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy import func, select, tuple_
from sqlalchemy.orm import Session

from lib_management.circulation import models as m
from lib_management.circulation import schemas as s
from lib_management.circulation import views as v
from lib_management.circulation.service import (
    RULES,
    active_policy,
    charge_balance,
    eligibility,
    total,
    view,
)
from lib_management.core import audit, idempotency
from lib_management.core.errors import (
    AppError,
    Conflict,
    Forbidden,
    NotFound,
    ValidationFailed,
)
from lib_management.core.pagination import Page, PageParams, encode_cursor, page_params
from lib_management.core.request_id import current_request_id
from lib_management.core.uow import UnitOfWork, get_uow
from lib_management.identity.auth import (
    Principal,
    require_permission,
    staff_reader_scope,
)

router = APIRouter()
Uow = Annotated[UnitOfWork, Depends(get_uow)]
Key = Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)]
Paging = Annotated[PageParams, Depends(page_params)]


def get(session: Session, model: Any, identifier: UUID, *, lock: bool = False) -> Any:
    statement = select(model).where(model.id == identifier)
    if lock:
        statement = statement.with_for_update().execution_options(
            populate_existing=True
        )
    row = session.scalar(statement)
    if row is None:
        raise NotFound()
    return row


def version(row: Any, expected: int) -> None:
    actual = row.version_no if isinstance(row, m.PolicyVersion) else row.version
    if actual != expected:
        raise Conflict("Dữ liệu đã thay đổi, vui lòng tải lại", code="VERSION_CONFLICT")


def paginate(
    session: Session, model: Any, paging: PageParams, *filters: Any
) -> dict[str, Any]:
    statement = select(model).where(*filters)
    if paging.cursor:
        try:
            stamp = datetime.fromisoformat(paging.cursor.k[0])
        except (IndexError, ValueError) as error:
            raise ValidationFailed("Cursor không hợp lệ") from error
        statement = statement.where(
            tuple_(model.created_at, model.id) > (stamp, paging.cursor.id)
        )
    rows = list(
        session.scalars(
            statement.order_by(model.created_at, model.id).limit(paging.limit + 1)
        )
    )
    more = len(rows) > paging.limit
    rows = rows[: paging.limit]
    return {
        "data": [view(row) for row in rows],
        "nextCursor": encode_cursor([rows[-1].created_at.isoformat()], rows[-1].id)
        if more and rows
        else None,
    }


def start(
    uow: UnitOfWork, principal: Principal, operation: str, key: str, body: Any
) -> idempotency.Begin:
    return idempotency.begin(
        uow.session,
        actor_id=principal.account_id,
        operation=operation,
        key=key,
        payload=body,
        ttl=timedelta(hours=24),
    )


def finish(
    uow: UnitOfWork,
    principal: Principal,
    begun: idempotency.Begin,
    operation: str,
    result: dict[str, Any],
    target: UUID | None = None,
) -> JSONResponse:
    audit.record(
        uow.session,
        actor_id=principal.account_id,
        action=operation,
        permission_code=operation,
        target_type=operation.split(".")[0],
        target_id=target,
        outcome="SUCCESS",
    )
    idempotency.complete(uow.session, begun, 201, result)
    uow.commit()
    return JSONResponse(result, status_code=201)


def replay(begun: idempotency.Begin) -> JSONResponse:
    return JSONResponse(begun.response_body, status_code=begun.response_status)


def reader_lock(session: Session, identifier: UUID) -> Any:
    from lib_management.readers.models import Reader

    return get(session, Reader, identifier, lock=True)


def require_eligible(session: Session, reader_id: UUID) -> m.PolicyVersion:
    result = eligibility(session, reader_id)
    if not result["allowed"]:
        raise AppError(
            422,
            "READER_NOT_ELIGIBLE",
            "Độc giả chưa đủ điều kiện",
            [{"reasons": result["reasons"]}],
        )
    return active_policy(session)


def issue(
    session: Session,
    principal: Principal,
    reader_id: UUID,
    copies: list[Any],
    policy: m.PolicyVersion,
) -> dict[str, Any]:
    from lib_management.readers.models import ReaderCard

    now = datetime.now(UTC)
    card = session.scalar(
        select(ReaderCard)
        .where(
            ReaderCard.reader_id == reader_id,
            ReaderCard.status == "ACTIVE",
            ReaderCard.expires_at > now,
        )
        .with_for_update()
    )
    if card is None:
        raise ValidationFailed("Thẻ không còn hiệu lực")
    loan = m.Loan(
        loan_no=f"L-{uuid4().hex[:20].upper()}",
        reader_id=reader_id,
        card_id=card.id,
        issued_by=principal.account_id,
        issued_at=now,
    )
    session.add(loan)
    session.flush()
    items = []
    for copy in copies:
        copy.status = "ON_LOAN"
        copy.version += 1
        item = m.LoanItem(
            loan_id=loan.id,
            copy_id=copy.id,
            issued_at=now,
            due_at=now + timedelta(days=policy.rules["initialLoanDays"]),
            policy_version_id=policy.id,
            applied_rules=policy.rules,
        )
        session.add(item)
        session.flush()
        items.append(
            {
                "loanItemId": str(item.id),
                "copyId": str(copy.id),
                "dueAt": item.due_at.isoformat(),
            }
        )
    return {
        "loanId": str(loan.id),
        "items": items,
        "policyVersionId": str(policy.id),
        "requestId": current_request_id() or "system",
    }


@router.get(
    "/policy-versions",
    operation_id="get_policy_versions",
    response_model=Page[v.PolicyVersion],
)
def policies(
    uow: Uow,
    principal: Annotated[Principal, Depends(require_permission("policy.write"))],
    paging: Paging,
) -> dict[str, Any]:
    return paginate(uow.session, m.PolicyVersion, paging)


@router.get(
    "/policy-versions/{id}",
    operation_id="get_policy_versions_id",
    response_model=v.PolicyVersion,
)
def get_policy(
    id: UUID,
    uow: Uow,
    principal: Annotated[Principal, Depends(require_permission("policy.write"))],
) -> Any:
    return get(uow.session, m.PolicyVersion, id)


@router.post(
    "/policy-versions",
    operation_id="post_policy_versions",
    status_code=201,
    response_model=v.PolicyVersion,
)
def create_policy(
    body: s.PolicyRequest,
    uow: Uow,
    key: Key,
    principal: Annotated[Principal, Depends(require_permission("policy.write"))],
) -> JSONResponse:
    if body.rulesSchemaVersion != 1 or body.rules != RULES:
        raise ValidationFailed("Quy định phải tuân thủ C01–C09 và schema v1")
    if body.effectiveFrom.tzinfo is None:
        raise ValidationFailed("effectiveFrom cần múi giờ")
    begun = start(uow, principal, "policy.write", key, body.model_dump(mode="json"))
    if begun.replay:
        return replay(begun)
    policy = m.PolicyVersion(
        effective_from=body.effectiveFrom,
        status="DRAFT",
        rules=body.rules,
        rules_schema_version=1,
    )
    uow.session.add(policy)
    uow.session.flush()
    return finish(uow, principal, begun, "policy.write", view(policy), policy.id)


@router.post(
    "/policy-versions/{id}/approval",
    operation_id="post_policy_versions_id_approval",
    status_code=201,
    response_model=v.PolicyVersion,
)
def approve_policy(
    id: UUID,
    body: s.VersionRequest,
    uow: Uow,
    key: Key,
    principal: Annotated[Principal, Depends(require_permission("policy.approve"))],
) -> JSONResponse:
    begun = start(
        uow, principal, "policy.approve", key, {"id": str(id), **body.model_dump()}
    )
    if begun.replay:
        return replay(begun)
    uow.session.execute(select(func.pg_advisory_xact_lock(8125493)))
    policy = get(uow.session, m.PolicyVersion, id, lock=True)
    version(policy, body.expectedVersion)
    now = datetime.now(UTC)
    if policy.status != "DRAFT" or policy.effective_from <= now:
        raise Conflict("Chỉ duyệt bản nháp có thời điểm hiệu lực trong tương lai")
    previous = uow.session.scalar(
        select(m.PolicyVersion)
        .where(m.PolicyVersion.status.in_(["ACTIVE", "SUPERSEDED"]))
        .order_by(m.PolicyVersion.effective_from.desc())
        .limit(1)
        .with_for_update()
    )
    if previous:
        if (
            previous.effective_from > now
            or previous.effective_from >= policy.effective_from
            or previous.effective_to is not None
        ):
            raise Conflict("Không được chèn hoặc ghi đè lịch đã duyệt")
        previous.effective_to = policy.effective_from
        uow.session.flush()
    policy.status = "ACTIVE"
    policy.approved_by = principal.account_id
    policy.approved_at = now
    uow.session.flush()
    return finish(uow, principal, begun, "policy.approve", view(policy), policy.id)


@router.post(
    "/loans",
    operation_id="post_loans",
    status_code=201,
    response_model=v.CheckoutReceipt,
)
def checkout(
    body: s.CheckoutRequest,
    uow: Uow,
    key: Key,
    principal: Annotated[Principal, Depends(require_permission("loan.checkout"))],
) -> JSONResponse:
    from lib_management.catalog.models import BookCopy

    if len(set(body.copyIds)) != len(body.copyIds):
        raise ValidationFailed("Không được lặp bản sách")
    begun = start(uow, principal, "loan.checkout", key, body.model_dump(mode="json"))
    if begun.replay:
        return replay(begun)
    edition_ids = list(
        uow.session.scalars(
            select(BookCopy.edition_id).where(BookCopy.id.in_(body.copyIds))
        )
    )
    lock_editions(uow.session, edition_ids)
    reader_lock(uow.session, body.readerId)
    policy = require_eligible(uow.session, body.readerId)
    copies = list(
        uow.session.scalars(
            select(BookCopy)
            .where(BookCopy.id.in_(body.copyIds))
            .order_by(BookCopy.id)
            .with_for_update()
        )
    )
    if len(copies) != len(body.copyIds):
        raise NotFound("Không tìm thấy bản sách")
    allocate_for = sorted(set(edition_ids))
    for edition_id in allocate_for:
        allocate(uow.session, edition_id)
    if any(copy.status != "AVAILABLE" for copy in copies):
        raise Conflict("Bản sách không sẵn sàng")
    result = issue(uow.session, principal, body.readerId, copies, policy)
    return finish(
        uow, principal, begun, "loan.checkout", result, UUID(result["loanId"])
    )


@router.get("/loans/{id}", operation_id="get_loans_id", response_model=v.Loan)
def loan_detail(
    id: UUID,
    uow: Uow,
    principal: Annotated[Principal, Depends(require_permission("reader.read"))],
) -> dict[str, Any]:
    loan = get(uow.session, m.Loan, id)
    if (
        principal.account.reader_id is not None
        and principal.account.reader_id != loan.reader_id
    ):
        raise NotFound()
    return view(loan)


@router.post(
    "/returns",
    operation_id="post_returns",
    status_code=201,
    response_model=v.ReturnReceipt,
)
def return_copy(
    body: s.ReturnRequest,
    uow: Uow,
    key: Key,
    principal: Annotated[Principal, Depends(require_permission("return.create"))],
) -> JSONResponse:
    from lib_management.catalog.models import BookCopy

    if body.condition != "GOOD" and "assessment.propose" not in principal.permissions:
        raise Forbidden("PERMISSION_DENIED", "Thiếu quyền assessment.propose")
    if (body.condition == "GOOD") == (body.assessment is not None):
        raise ValidationFailed("Đề xuất phí chỉ bắt buộc với hỏng/mất")
    begun = start(uow, principal, "return.create", key, body.model_dump(mode="json"))
    if begun.replay:
        return replay(begun)
    item = get(uow.session, m.LoanItem, body.loanItemId)
    loan = get(uow.session, m.Loan, item.loan_id)
    copy = get(uow.session, BookCopy, item.copy_id)
    lock_editions(uow.session, [copy.edition_id])
    reader_lock(uow.session, loan.reader_id)
    copy = get(uow.session, BookCopy, item.copy_id, lock=True)
    item = get(uow.session, m.LoanItem, item.id, lock=True)
    if item.closed_at is not None:
        raise Conflict("Bản sách đã được đóng")
    now = datetime.now(UTC)
    item.closed_at = now
    item.closure_reason = "LOST" if body.condition == "LOST" else "RETURNED"
    item.version += 1
    event = m.ReturnEvent(
        loan_item_id=item.id,
        return_kind=item.closure_reason,
        condition=None
        if body.condition == "LOST"
        else ("DAMAGED" if body.condition == "DAMAGE" else "GOOD"),
        returned_at=now,
        processed_by=principal.account_id,
        notes=body.notes,
    )
    uow.session.add(event)
    copy.status = {"GOOD": "AVAILABLE", "DAMAGE": "REPAIR", "LOST": "LOST"}[
        body.condition
    ]
    copy.version += 1
    uow.session.flush()
    charges = []
    late_days = max(
        0,
        (
            now.astimezone(ZoneInfo("Asia/Ho_Chi_Minh")).date()
            - item.due_at.astimezone(ZoneInfo("Asia/Ho_Chi_Minh")).date()
        ).days,
    )
    rate = Decimal(item.applied_rules["overdueFinePerDay"])
    if late_days and rate:
        charge = m.FineCharge(
            reader_id=loan.reader_id,
            loan_item_id=item.id,
            policy_version_id=item.policy_version_id,
            reason="LATE",
            assessed_amount=late_days * rate,
            late_days=late_days,
            unit_rate=rate,
            calculation={"lateDays": late_days, "unitRate": str(rate)},
            assessed_by=principal.account_id,
        )
        uow.session.add(charge)
        uow.session.flush()
        charges.append(view(charge))
    assessment_id = None
    if body.assessment is not None:
        assessment = m.ChargeAssessment(
            reader_id=loan.reader_id,
            return_event_id=event.id,
            kind=body.condition,
            proposed_amount=Decimal(body.assessment.proposedAmount),
            reason=body.assessment.reason,
            proposed_by=principal.account_id,
            status="PENDING",
        )
        uow.session.add(assessment)
        uow.session.flush()
        assessment_id = str(assessment.id)
    if body.condition == "GOOD":
        allocate(uow.session, copy.edition_id)
    return finish(
        uow,
        principal,
        begun,
        "return.create",
        {
            "returnEvent": view(event),
            "copyStatus": copy.status,
            "charges": charges,
            "assessmentId": assessment_id,
        },
        event.id,
    )


@router.post(
    "/loans/{id}/renewals",
    operation_id="post_loans_id_renewals",
    status_code=201,
    response_model=v.RenewalEvent,
)
def renew(
    id: UUID,
    body: s.RenewRequest,
    uow: Uow,
    key: Key,
    principal: Annotated[Principal, Depends(require_permission("loan.renew"))],
) -> JSONResponse:
    begun = start(
        uow, principal, "loan.renew", key, {"id": str(id), **body.model_dump()}
    )
    if begun.replay:
        return replay(begun)
    from lib_management.catalog.models import BookCopy

    loan = get(uow.session, m.Loan, id)
    copy_ids = list(
        uow.session.scalars(
            select(m.LoanItem.copy_id).where(
                m.LoanItem.loan_id == id, m.LoanItem.closed_at.is_(None)
            )
        )
    )
    edition_ids = list(
        uow.session.scalars(
            select(BookCopy.edition_id).where(BookCopy.id.in_(copy_ids))
        )
    )
    lock_editions(uow.session, edition_ids)
    reader_lock(uow.session, loan.reader_id)
    list(
        uow.session.scalars(
            select(BookCopy)
            .where(BookCopy.id.in_(copy_ids))
            .order_by(BookCopy.id)
            .with_for_update()
        )
    )
    loan = get(uow.session, m.Loan, id, lock=True)
    version(loan, body.expectedVersion)
    policy = require_eligible(uow.session, loan.reader_id)
    if loan.renewal_count >= policy.rules["maxRenewals"]:
        raise Conflict("Đã hết số lần gia hạn")
    items = list(
        uow.session.scalars(
            select(m.LoanItem)
            .where(m.LoanItem.loan_id == id, m.LoanItem.closed_at.is_(None))
            .order_by(m.LoanItem.id)
            .with_for_update()
        )
    )
    if not items:
        raise Conflict("Phiếu không còn mục đang mượn")
    editions = select(BookCopy.edition_id).where(
        BookCopy.id.in_([i.copy_id for i in items])
    )
    if uow.session.scalar(
        select(m.Reservation.id)
        .where(
            m.Reservation.edition_id.in_(editions),
            m.Reservation.status.in_(["QUEUED", "READY"]),
        )
        .limit(1)
    ):
        raise Conflict("Sách đang có đặt trước")
    event = m.RenewalEvent(
        loan_id=id,
        sequence_no=loan.renewal_count + 1,
        actor_id=principal.account_id,
        renewed_at=datetime.now(UTC),
        policy_version_id=policy.id,
        request_id=current_request_id() or "system",
    )
    uow.session.add(event)
    uow.session.flush()
    for item in items:
        new_due = item.due_at + timedelta(days=policy.rules["renewalDays"])
        uow.session.add(
            m.RenewalItem(
                renewal_event_id=event.id,
                loan_item_id=item.id,
                old_due_at=item.due_at,
                new_due_at=new_due,
                applied_rules=policy.rules,
            )
        )
        item.due_at = new_due
        item.version += 1
    loan.renewal_count += 1
    loan.version += 1
    return finish(uow, principal, begun, "loan.renew", view(event), event.id)


@router.get(
    "/fine-charges", operation_id="get_fine_charges", response_model=Page[v.FineCharge]
)
def charges(
    uow: Uow,
    paging: Paging,
    principal: Annotated[Principal, Depends(require_permission("finance.read"))],
    readerId: UUID | None = None,
) -> dict[str, Any]:
    if not staff_reader_scope(principal):
        raise Forbidden("PERMISSION_DENIED", "Sử dụng mục tài khoản của tôi")
    return paginate(
        uow.session,
        m.FineCharge,
        paging,
        *([m.FineCharge.reader_id == readerId] if readerId else []),
    )


@router.get(
    "/charge-assessments",
    operation_id="get_charge_assessments",
    response_model=Page[v.ChargeAssessment],
)
def assessments(
    uow: Uow,
    paging: Paging,
    principal: Annotated[Principal, Depends(require_permission("assessment.decide"))],
) -> dict[str, Any]:
    page = paginate(uow.session, m.ChargeAssessment, paging)
    for row in page["data"]:
        for key in [
            "proposed_by",
            "decided_by",
            "decided_at",
            "decision_reason",
            "fine_charge_id",
            "created_at",
        ]:
            row.pop(key, None)
    return page


@router.post(
    "/charge-assessments/{id}/decisions",
    operation_id="post_charge_assessments_id_decisions",
    status_code=201,
    response_model=v.ChargeAssessment,
)
def decide(
    id: UUID,
    body: s.DecisionRequest,
    uow: Uow,
    key: Key,
    principal: Annotated[Principal, Depends(require_permission("assessment.decide"))],
) -> JSONResponse:
    begun = start(
        uow, principal, "assessment.decide", key, {"id": str(id), **body.model_dump()}
    )
    if begun.replay:
        return replay(begun)
    assessment = get(uow.session, m.ChargeAssessment, id)
    reader_lock(uow.session, assessment.reader_id)
    assessment = get(uow.session, m.ChargeAssessment, id, lock=True)
    version(assessment, body.expectedVersion)
    if assessment.status != "PENDING":
        raise Conflict("Hồ sơ đã được quyết định")
    event = get(uow.session, m.ReturnEvent, assessment.return_event_id)
    item = get(uow.session, m.LoanItem, event.loan_item_id)
    approved_amount = Decimal(body.amount)
    if approved_amount > 0:
        charge = m.FineCharge(
            reader_id=assessment.reader_id,
            loan_item_id=item.id,
            policy_version_id=item.policy_version_id,
            reason=assessment.kind,
            assessed_amount=approved_amount,
            calculation={"assessmentId": str(id)},
            manual_reason=body.reason,
            assessed_by=principal.account_id,
        )
        uow.session.add(charge)
        uow.session.flush()
        assessment.fine_charge_id = charge.id
        assessment.status = "ASSESSED"
    else:
        assessment.status = "CLOSED_NO_CHARGE"
    assessment.approved_amount = approved_amount
    assessment.decided_by = principal.account_id
    assessment.decided_at = datetime.now(UTC)
    assessment.decision_reason = body.reason
    assessment.version += 1
    uow.session.flush()
    projection = view(assessment)
    for field in [
        "proposed_by",
        "decided_by",
        "decided_at",
        "decision_reason",
        "fine_charge_id",
        "created_at",
    ]:
        projection.pop(field, None)
    return finish(uow, principal, begun, "assessment.decide", projection, id)


@router.post(
    "/payments", operation_id="post_payments", status_code=201, response_model=v.Payment
)
def payment(
    body: s.PaymentRequest,
    uow: Uow,
    key: Key,
    principal: Annotated[Principal, Depends(require_permission("payment.collect"))],
) -> JSONResponse:
    amount = Decimal(body.amount)
    if amount <= 0 or sum(Decimal(row.amount) for row in body.allocations) != amount:
        raise ValidationFailed("Tổng phân bổ phải bằng tiền thu và lớn hơn 0")
    if len({row.chargeId for row in body.allocations}) != len(body.allocations):
        raise ValidationFailed("Khoản phí phân bổ không được lặp")
    begun = start(uow, principal, "payment.collect", key, body.model_dump(mode="json"))
    if begun.replay:
        return replay(begun)
    reader_lock(uow.session, body.readerId)
    for allocation in sorted(body.allocations, key=lambda row: str(row.chargeId)):
        charge = get(uow.session, m.FineCharge, allocation.chargeId, lock=True)
        if charge.reader_id != body.readerId:
            raise ValidationFailed("Khoản phí không thuộc độc giả")
        if Decimal(allocation.amount) <= 0 or Decimal(
            allocation.amount
        ) > charge_balance(uow.session, charge.id):
            raise Conflict("Phân bổ vượt dư nợ")
    row = m.Payment(
        reader_id=body.readerId,
        receipt_no=f"P-{uuid4().hex[:20].upper()}",
        amount=amount,
        method=body.method,
        received_at=datetime.now(UTC),
        received_by=principal.account_id,
        reference=body.reference,
    )
    uow.session.add(row)
    uow.session.flush()
    for allocation in body.allocations:
        uow.session.add(
            m.PaymentAllocation(
                payment_id=row.id,
                charge_id=allocation.chargeId,
                amount=Decimal(allocation.amount),
            )
        )
    return finish(uow, principal, begun, "payment.collect", view(row), row.id)


@router.post(
    "/fine-charges/{id}/waivers",
    operation_id="post_fine_charges_id_waivers",
    status_code=201,
    response_model=v.Waiver,
)
def waive(
    id: UUID,
    body: s.WaiverRequest,
    uow: Uow,
    key: Key,
    principal: Annotated[Principal, Depends(require_permission("charge.waive"))],
) -> JSONResponse:
    begun = start(
        uow, principal, "charge.waive", key, {"id": str(id), **body.model_dump()}
    )
    if begun.replay:
        return replay(begun)
    charge = get(uow.session, m.FineCharge, id)
    reader_lock(uow.session, charge.reader_id)
    charge = get(uow.session, m.FineCharge, id, lock=True)
    amount = Decimal(body.amount)
    if amount <= 0 or amount > charge_balance(uow.session, id):
        raise Conflict("Tiền miễn vượt dư nợ")
    waiver = m.Waiver(
        charge_id=id,
        amount=amount,
        approved_by=principal.account_id,
        reason=body.reason,
    )
    uow.session.add(waiver)
    uow.session.flush()
    return finish(uow, principal, begun, "charge.waive", view(waiver), waiver.id)


@router.post(
    "/ledger-reversals",
    operation_id="post_ledger_reversals",
    status_code=201,
    response_model=v.LedgerReversalReceipt,
)
def reverse(
    body: s.ReversalRequest,
    uow: Uow,
    key: Key,
    principal: Annotated[Principal, Depends(require_permission("ledger.reverse"))],
) -> JSONResponse:
    amount = Decimal(body.amount)
    if amount <= 0:
        raise ValidationFailed("Số tiền đảo phải lớn hơn 0")
    begun = start(uow, principal, "ledger.reverse", key, body.model_dump(mode="json"))
    if begun.replay:
        return replay(begun)
    if body.entryType == "WAIVER":
        original = get(uow.session, m.Waiver, body.entryId)
        charge = get(uow.session, m.FineCharge, original.charge_id)
        reader_lock(uow.session, charge.reader_id)
        original = get(uow.session, m.Waiver, original.id, lock=True)
        already = total(
            uow.session, m.WaiverReversal, m.WaiverReversal.waiver_id == original.id
        )
        if amount > original.amount - already:
            raise Conflict("Đảo vượt chứng từ gốc")
        reversal: Any = m.WaiverReversal(
            waiver_id=original.id,
            amount=amount,
            actor_id=principal.account_id,
            reason=body.reason,
        )
    else:
        original = get(uow.session, m.Payment, body.entryId)
        reader_lock(uow.session, original.reader_id)
        original = get(uow.session, m.Payment, original.id, lock=True)
        if body.entryType == "ALLOCATION":
            if body.chargeId is None:
                raise ValidationFailed("chargeId bắt buộc khi đảo phân bổ")
            allocation = uow.session.get(
                m.PaymentAllocation, (original.id, body.chargeId)
            )
            if allocation is None:
                raise NotFound()
            already = total(
                uow.session,
                m.AllocationReversal,
                (m.AllocationReversal.payment_id == original.id)
                & (m.AllocationReversal.charge_id == body.chargeId),
            )
            if amount > allocation.amount - already:
                raise Conflict("Đảo vượt phân bổ gốc")
            reversal = m.AllocationReversal(
                payment_id=original.id,
                charge_id=body.chargeId,
                amount=amount,
                actor_id=principal.account_id,
                reason=body.reason,
            )
        else:
            already = total(
                uow.session,
                m.PaymentReversal,
                m.PaymentReversal.payment_id == original.id,
            )
            if amount > original.amount - already:
                raise Conflict("Đảo vượt tiền thu gốc")
            allocations = list(
                uow.session.scalars(
                    select(m.PaymentAllocation)
                    .where(m.PaymentAllocation.payment_id == original.id)
                    .order_by(m.PaymentAllocation.charge_id)
                    .with_for_update()
                )
            )
            remaining = amount
            for allocation in allocations:
                reversed_amount = total(
                    uow.session,
                    m.AllocationReversal,
                    (m.AllocationReversal.payment_id == original.id)
                    & (m.AllocationReversal.charge_id == allocation.charge_id),
                )
                part = min(remaining, allocation.amount - reversed_amount)
                if part > 0:
                    uow.session.add(
                        m.AllocationReversal(
                            payment_id=original.id,
                            charge_id=allocation.charge_id,
                            amount=part,
                            actor_id=principal.account_id,
                            reason=body.reason,
                        )
                    )
                    remaining -= part
                if not remaining:
                    break
            reversal = m.PaymentReversal(
                payment_id=original.id,
                amount=amount,
                actor_id=principal.account_id,
                reason=body.reason,
            )
    uow.session.add(reversal)
    uow.session.flush()
    return finish(
        uow,
        principal,
        begun,
        "ledger.reverse",
        {
            "reversalType": body.entryType,
            "reversalId": str(reversal.id),
            "requestId": current_request_id() or "system",
        },
        reversal.id,
    )


@router.get(
    "/readers/{id}/history",
    operation_id="get_readers_id_history",
    response_model=Page[v.LoanItem],
)
def history(
    id: UUID,
    uow: Uow,
    paging: Paging,
    principal: Annotated[Principal, Depends(require_permission("reader.read"))],
) -> dict[str, Any]:
    reader_lock(uow.session, id)
    if not staff_reader_scope(principal) and principal.account.reader_id != id:
        raise NotFound()
    return paginate(
        uow.session,
        m.LoanItem,
        paging,
        m.LoanItem.loan_id.in_(select(m.Loan.id).where(m.Loan.reader_id == id)),
    )


@router.get("/overdue-items", operation_id="get_overdue_items")
def overdue(
    uow: Uow,
    paging: Paging,
    principal: Annotated[Principal, Depends(require_permission("overdue.read"))],
) -> dict[str, Any]:
    """F19: OPEN items past due, computed at query time (no stored overdue flag)."""
    from lib_management.catalog.models import BookCopy, BookEdition
    from lib_management.readers.models import Reader

    now = datetime.now(UTC)
    statement = (
        select(m.LoanItem, m.Loan, BookCopy, BookEdition.title, Reader)
        .join(m.Loan, m.Loan.id == m.LoanItem.loan_id)
        .join(BookCopy, BookCopy.id == m.LoanItem.copy_id)
        .join(BookEdition, BookEdition.id == BookCopy.edition_id)
        .join(Reader, Reader.id == m.Loan.reader_id)
        .where(m.LoanItem.closed_at.is_(None), m.LoanItem.due_at < now)
    )
    if paging.cursor:
        statement = statement.where(m.LoanItem.id > paging.cursor.id)
    rows = uow.session.execute(
        statement.order_by(m.LoanItem.id).limit(paging.limit + 1)
    ).all()
    more = len(rows) > paging.limit
    rows = rows[: paging.limit]
    return {
        "data": [
            {
                "loanItem": view(item),
                "loan": view(loan),
                "copy": view(copy),
                "title": title,
                "reader": {
                    "id": str(reader.id),
                    "reader_code": reader.reader_code,
                    "full_name": reader.full_name,
                },
                # Whole days past due on the library calendar (Asia/Ho_Chi_Minh).
                "lateDays": max(
                    0,
                    (
                        now.astimezone(ZoneInfo("Asia/Ho_Chi_Minh")).date()
                        - item.due_at.astimezone(ZoneInfo("Asia/Ho_Chi_Minh")).date()
                    ).days,
                ),
            }
            for item, loan, copy, title, reader in rows
        ],
        "nextCursor": encode_cursor([], rows[-1][0].id) if more else None,
    }


def own_reader(principal: Principal) -> UUID:
    if principal.account.reader_id is None:
        raise NotFound("Tài khoản chưa liên kết độc giả")
    return principal.account.reader_id


@router.get("/me/loans", operation_id="get_me_loans", response_model=Page[v.LoanItem])
def my_loans(
    uow: Uow,
    paging: Paging,
    principal: Annotated[Principal, Depends(require_permission("reader.read"))],
) -> dict[str, Any]:
    return paginate(
        uow.session,
        m.LoanItem,
        paging,
        m.LoanItem.loan_id.in_(
            select(m.Loan.id).where(m.Loan.reader_id == own_reader(principal))
        ),
    )


@router.get(
    "/me/fine-charges",
    operation_id="get_me_fine_charges",
    response_model=Page[v.FineCharge],
)
def my_charges(
    uow: Uow,
    paging: Paging,
    principal: Annotated[Principal, Depends(require_permission("finance.read"))],
) -> dict[str, Any]:
    return paginate(
        uow.session,
        m.FineCharge,
        paging,
        m.FineCharge.reader_id == own_reader(principal),
    )


@router.get(
    "/reservations", operation_id="get_reservations", response_model=Page[v.Reservation]
)
def reservations(
    uow: Uow,
    paging: Paging,
    principal: Annotated[Principal, Depends(require_permission("reservation.read"))],
    readerId: UUID | None = None,
) -> dict[str, Any]:
    if not staff_reader_scope(principal):
        raise Forbidden("PERMISSION_DENIED", "Sử dụng mục tài khoản của tôi")
    return paginate(
        uow.session,
        m.Reservation,
        paging,
        *([m.Reservation.reader_id == readerId] if readerId else []),
    )


@router.get(
    "/me/reservations",
    operation_id="get_me_reservations",
    response_model=Page[v.Reservation],
)
def my_reservations(
    uow: Uow,
    paging: Paging,
    principal: Annotated[Principal, Depends(require_permission("reservation.read"))],
) -> dict[str, Any]:
    return paginate(
        uow.session,
        m.Reservation,
        paging,
        m.Reservation.reader_id == own_reader(principal),
    )


def lock_editions(session: Session, edition_ids: list[UUID]) -> None:
    from lib_management.catalog.models import BookEdition

    list(
        session.scalars(
            select(BookEdition)
            .where(BookEdition.id.in_(edition_ids))
            .order_by(BookEdition.id)
            .with_for_update()
        )
    )


def allocate(session: Session, edition_id: UUID) -> None:
    """Allocate available copies to the FIFO queue while edition is locked."""
    from lib_management.catalog.models import BookCopy

    now = datetime.now(UTC)
    queued = list(
        session.scalars(
            select(m.Reservation)
            .where(
                m.Reservation.edition_id == edition_id, m.Reservation.status == "QUEUED"
            )
            .order_by(m.Reservation.created_at, m.Reservation.id)
            .with_for_update()
        )
    )
    copies = list(
        session.scalars(
            select(BookCopy)
            .where(BookCopy.edition_id == edition_id, BookCopy.status == "AVAILABLE")
            .order_by(BookCopy.id)
            .with_for_update()
        )
    )
    for reservation, copy in zip(queued, copies, strict=False):
        reservation.status = "READY"
        reservation.copy_id = copy.id
        reservation.ready_at = now
        reservation.ready_expires_at = now + timedelta(
            days=reservation.applied_rules["readyHoldDays"]
        )
        reservation.version += 1
        copy.status = "HELD"
        copy.version += 1
    session.flush()


@router.post(
    "/reservations",
    operation_id="post_reservations",
    status_code=201,
    response_model=v.Reservation,
)
def hold(
    body: s.HoldRequest,
    uow: Uow,
    key: Key,
    principal: Annotated[Principal, Depends(require_permission("reservation.create"))],
) -> JSONResponse:
    from lib_management.catalog.models import BookEdition

    reader_id = body.readerId or own_reader(principal)
    if (
        principal.account.reader_id is not None
        and reader_id != principal.account.reader_id
    ):
        raise NotFound()
    begun = start(
        uow, principal, "reservation.create", key, body.model_dump(mode="json")
    )
    if begun.replay:
        return replay(begun)
    edition = get(uow.session, BookEdition, body.editionId, lock=True)
    if edition.status != "ACTIVE":
        raise ValidationFailed("Ấn bản không hoạt động")
    reader_lock(uow.session, reader_id)
    policy = require_eligible(uow.session, reader_id)
    if uow.session.scalar(
        select(m.Reservation.id)
        .where(
            m.Reservation.reader_id == reader_id,
            m.Reservation.edition_id == body.editionId,
            m.Reservation.status.in_(["QUEUED", "READY"]),
        )
        .limit(1)
    ):
        raise Conflict("Độc giả đã đặt trước ấn bản này")
    reservation = m.Reservation(
        reader_id=reader_id,
        edition_id=body.editionId,
        status="QUEUED",
        policy_version_id=policy.id,
        applied_rules=policy.rules,
    )
    uow.session.add(reservation)
    uow.session.flush()
    allocate(uow.session, body.editionId)
    return finish(
        uow, principal, begun, "reservation.create", view(reservation), reservation.id
    )


@router.post(
    "/reservations/{id}/cancellations",
    operation_id="post_reservations_id_cancellations",
    status_code=201,
    response_model=v.Reservation,
)
def cancel_hold(
    id: UUID,
    body: s.ReasonRequest,
    uow: Uow,
    key: Key,
    principal: Annotated[Principal, Depends(require_permission("reservation.cancel"))],
) -> JSONResponse:
    from lib_management.catalog.models import BookCopy

    begun = start(
        uow, principal, "reservation.cancel", key, {"id": str(id), **body.model_dump()}
    )
    if begun.replay:
        return replay(begun)
    reservation = get(uow.session, m.Reservation, id)
    if (
        principal.account.reader_id is not None
        and principal.account.reader_id != reservation.reader_id
    ):
        raise NotFound()
    lock_editions(uow.session, [reservation.edition_id])
    reader_lock(uow.session, reservation.reader_id)
    copy = (
        get(uow.session, BookCopy, reservation.copy_id, lock=True)
        if reservation.copy_id
        else None
    )
    reservation = get(uow.session, m.Reservation, id, lock=True)
    if body.expectedVersion:
        version(reservation, body.expectedVersion)
    if reservation.status not in ["QUEUED", "READY"]:
        raise Conflict("Đặt trước không còn hoạt động")
    reservation.status = "CANCELLED"
    reservation.cancellation_reason = body.reason
    reservation.version += 1
    if copy:
        copy.status = "AVAILABLE"
        copy.version += 1
    uow.session.flush()
    allocate(uow.session, reservation.edition_id)
    return finish(uow, principal, begun, "reservation.cancel", view(reservation), id)


@router.post(
    "/reservations/{id}/pickups",
    operation_id="post_reservations_id_pickups",
    status_code=201,
    response_model=v.CheckoutReceipt,
)
def pickup_hold(
    id: UUID,
    body: s.VersionRequest,
    uow: Uow,
    key: Key,
    principal: Annotated[Principal, Depends(require_permission("reservation.pickup"))],
) -> JSONResponse:
    from lib_management.catalog.models import BookCopy

    begun = start(
        uow, principal, "reservation.pickup", key, {"id": str(id), **body.model_dump()}
    )
    if begun.replay:
        return replay(begun)
    reservation = get(uow.session, m.Reservation, id)
    lock_editions(uow.session, [reservation.edition_id])
    reader_lock(uow.session, reservation.reader_id)
    copy = (
        get(uow.session, BookCopy, reservation.copy_id, lock=True)
        if reservation.copy_id
        else None
    )
    reservation = get(uow.session, m.Reservation, id, lock=True)
    version(reservation, body.expectedVersion)
    if (
        reservation.status != "READY"
        or reservation.ready_expires_at <= datetime.now(UTC)
        or copy is None
    ):
        raise Conflict("Đặt trước chưa sẵn sàng hoặc đã hết hạn")
    if copy.status != "HELD":
        raise Conflict("Bản sách không còn được giữ")
    policy = require_eligible(uow.session, reservation.reader_id)
    result = issue(uow.session, principal, reservation.reader_id, [copy], policy)
    reservation.status = "FULFILLED"
    reservation.fulfilled_loan_item_id = UUID(result["items"][0]["loanItemId"])
    reservation.version += 1
    return finish(uow, principal, begun, "reservation.pickup", result, id)


@router.get("/loans", operation_id="get_loans")
def lookup_loans(
    request: Request,
    uow: Uow,
    paging: Paging,
    principal: Annotated[Principal, Depends(require_permission("reader.read"))],
    readerId: UUID | None = None,
    barcode: Annotated[str | None, Query(min_length=1, max_length=64)] = None,
    cardNumber: Annotated[str | None, Query(min_length=1, max_length=64)] = None,
    status: Annotated[str, Query(pattern="^(OPEN|ALL)$")] = "OPEN",
) -> dict[str, Any]:
    from lib_management.catalog.models import BookCopy
    from lib_management.readers.models import ReaderCard

    if not staff_reader_scope(principal):
        raise Forbidden("PERMISSION_DENIED", "Tra cứu phiếu dành cho nhân viên")
    statement = select(m.LoanItem).join(m.Loan, m.Loan.id == m.LoanItem.loan_id)
    if readerId:
        statement = statement.where(m.Loan.reader_id == readerId)
    if barcode:
        statement = statement.join(BookCopy, BookCopy.id == m.LoanItem.copy_id).where(
            BookCopy.barcode == barcode
        )
    if cardNumber:
        statement = statement.join(ReaderCard, ReaderCard.id == m.Loan.card_id).where(
            ReaderCard.card_no == cardNumber
        )
    if status == "OPEN":
        statement = statement.where(m.LoanItem.closed_at.is_(None))
    if paging.cursor:
        statement = statement.where(m.LoanItem.id > paging.cursor.id)
    items = list(
        uow.session.scalars(statement.order_by(m.LoanItem.id).limit(paging.limit + 1))
    )
    more = len(items) > paging.limit
    items = items[: paging.limit]
    loans = {
        loan.id: loan
        for loan in uow.session.scalars(
            select(m.Loan).where(m.Loan.id.in_([row.loan_id for row in items]))
        )
    }
    copies = {
        copy.id: copy
        for copy in uow.session.scalars(
            select(BookCopy).where(BookCopy.id.in_([row.copy_id for row in items]))
        )
    }
    return {
        "data": [
            {
                "loan": view(loans[item.loan_id]),
                "loanItem": view(item),
                "copy": view(copies[item.copy_id]),
            }
            for item in items
        ],
        "nextCursor": encode_cursor([], items[-1].id) if more else None,
    }


@router.post(
    "/copies/{id}/disposal",
    operation_id="post_copies_id_disposal",
    status_code=201,
    response_model=v.BookCopy,
)
def dispose(
    id: UUID,
    body: s.ReasonRequest,
    uow: Uow,
    key: Key,
    principal: Annotated[Principal, Depends(require_permission("copy.dispose"))],
) -> JSONResponse:
    from lib_management.catalog.models import BookCopy

    begun = start(
        uow, principal, "copy.dispose", key, {"id": str(id), **body.model_dump()}
    )
    if begun.replay:
        return replay(begun)
    copy = get(uow.session, BookCopy, id)
    lock_editions(uow.session, [copy.edition_id])
    copy = get(uow.session, BookCopy, id, lock=True)
    if body.expectedVersion:
        version(copy, body.expectedVersion)
    if copy.status not in ["AVAILABLE", "REPAIR", "LOST"]:
        raise Conflict("Chỉ thanh lý bản sách không còn cho mượn hoặc giữ chỗ")
    copy.status = "RETIRED"
    copy.version += 1
    audit.record(
        uow.session,
        actor_id=principal.account_id,
        action="copy.disposal.reason",
        target_type="book_copy",
        target_id=id,
        outcome="SUCCESS",
        metadata={"reason": body.reason},
    )
    return finish(uow, principal, begun, "copy.dispose", view(copy), id)
