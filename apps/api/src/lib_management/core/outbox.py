"""Transactional outbox: events commit with the business change."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from lib_management.core.request_id import current_request_id
from lib_management.platform.models import OutboxEvent

SCHEMA_VERSION = 1


def publish(
    session: Session,
    *,
    aggregate_type: str,
    aggregate_id: uuid.UUID,
    event_type: str,
    data: dict[str, Any],
) -> uuid.UUID:
    """Writes an envelope v1 (event-job-contracts.md). No email/secret in data."""
    event_id = uuid.uuid4()
    envelope = {
        "schemaVersion": SCHEMA_VERSION,
        "eventId": str(event_id),
        "eventType": event_type,
        "occurredAt": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "requestId": current_request_id() or "system",
        "aggregateType": aggregate_type,
        "aggregateId": str(aggregate_id),
        "data": data,
    }
    session.add(
        OutboxEvent(
            id=event_id,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_type=event_type,
            payload=envelope,
        )
    )
    return event_id
