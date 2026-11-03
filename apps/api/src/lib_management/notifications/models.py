"""Reader notifications and consent (database-design.md, schema bổ sung; F24)."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    false,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from lib_management.models import Base, created_at, uuid_pk


class Notification(Base):
    __tablename__ = "notification"
    __table_args__ = (
        CheckConstraint("kind IN ('READY','OVERDUE')", name="kind"),
        CheckConstraint(
            "kind <> 'READY' OR reservation_id IS NOT NULL", name="ready_reservation"
        ),
    )
    id: Mapped[uuid.UUID] = uuid_pk()
    event_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("outbox_event.id"))
    reader_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("reader.id"), index=True)
    kind: Mapped[str] = mapped_column(String(16))
    reservation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("reservation.id")
    )
    summary: Mapped[str] = mapped_column(Text)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    dedupe_key: Mapped[str] = mapped_column(String(200), unique=True)
    created_at: Mapped[datetime] = created_at()


class NotificationDelivery(Base):
    __tablename__ = "notification_delivery"
    __table_args__ = (
        UniqueConstraint("notification_id", "channel"),
        CheckConstraint("channel IN ('EMAIL')", name="channel"),
        CheckConstraint(
            "status IN ('QUEUED','SENDING','DELIVERED','FAILED','SKIPPED')",
            name="status",
        ),
    )
    id: Mapped[uuid.UUID] = uuid_pk()
    notification_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("notification.id"))
    channel: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16))
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("job.id"))
    provider_message_id: Mapped[str | None] = mapped_column(Text)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error_code: Mapped[str | None] = mapped_column(Text)


class NotificationPreference(Base):
    """Consent lives apart from Reader.email: an address is not an opt-in."""

    __tablename__ = "notification_preference"
    reader_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reader.id"), primary_key=True
    )
    email_consent: Mapped[bool] = mapped_column(Boolean, server_default=false())
    changed_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("account.id"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
