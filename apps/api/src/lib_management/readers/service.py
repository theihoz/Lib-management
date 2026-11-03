"""Reader commands, including calendar-based policy card validity."""

import calendar
import uuid
from datetime import date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from lib_management.catalog.service import changed, get
from lib_management.core.errors import Conflict, ValidationFailed
from lib_management.readers import models, schemas

LOCAL_ZONE = ZoneInfo("Asia/Ho_Chi_Minh")


def age_on(birth_date: date, on: date) -> int:
    return (
        on.year
        - birth_date.year
        - ((on.month, on.day) < (birth_date.month, birth_date.day))
    )


def add_calendar_months(value: datetime, months: int) -> datetime:
    year, month_index = divmod(value.year * 12 + value.month - 1 + months, 12)
    day = min(value.day, calendar.monthrange(year, month_index + 1)[1])
    return value.replace(year=year, month=month_index + 1, day=day)


def create(
    session: Session, payload: schemas.ReaderCreate, actor_id: uuid.UUID
) -> models.Reader:
    if payload.birth_date > datetime.now(LOCAL_ZONE).date():
        raise ValidationFailed("Ngày sinh không được trong tương lai")
    row = models.Reader(**payload.model_dump(), status="ACTIVE")
    session.add(row)
    changed(session, row, actor_id, "reader.create", "reader.write")
    return row


def patch(
    session: Session,
    identity: uuid.UUID,
    payload: schemas.ReaderPatch,
    actor_id: uuid.UUID,
) -> models.Reader:
    row = get(session, models.Reader, identity, lock=True)
    data = payload.model_dump(exclude_unset=True)
    if data.pop("expected_version") != row.version:
        raise Conflict("Phiên bản đã thay đổi", code="VERSION_CONFLICT")
    if "birth_date" in data and data["birth_date"] > datetime.now(LOCAL_ZONE).date():
        raise ValidationFailed("Ngày sinh không được trong tương lai")
    for key, value in data.items():
        setattr(row, key, value)
    row.version += 1
    changed(session, row, actor_id, "reader.update", "reader.write")
    return row


def issue_card(
    session: Session, identity: uuid.UUID, actor_id: uuid.UUID
) -> models.ReaderCard:
    from lib_management.circulation.service import active_policy

    reader = get(session, models.Reader, identity, lock=True)
    now = datetime.now(LOCAL_ZONE)
    policy = active_policy(session, now)
    age = age_on(reader.birth_date, now.date())
    if reader.status != "ACTIVE":
        raise ValidationFailed("Độc giả không hoạt động")
    if not policy.rules["minReaderAge"] <= age <= policy.rules["maxReaderAge"]:
        raise ValidationFailed("Tuổi độc giả ngoài khoảng được cấp thẻ")
    # Reissue preserves the prior card records while invalidating their future use.
    for card in session.scalars(
        select(models.ReaderCard)
        .where(
            models.ReaderCard.reader_id == identity,
            models.ReaderCard.status == "ACTIVE",
        )
        .with_for_update()
    ):
        card.status = "REVOKED"
        card.version += 1
        changed(session, card, actor_id, "card.revoke_for_reissue", "card.issue")
    card = models.ReaderCard(
        reader_id=identity,
        card_no=f"CARD-{uuid.uuid4().hex.upper()}",
        issued_at=now,
        expires_at=add_calendar_months(now, policy.rules["cardValidityMonths"]),
        status="ACTIVE",
        issued_by=actor_id,
        policy_version_id=policy.id,
    )
    session.add(card)
    changed(session, card, actor_id, "card.issue", "card.issue")
    return card
