"""Idempotency-Key handling scoped by actor + operation + key.

The PENDING record and the business result commit in the same transaction,
so a failed command leaves nothing behind and the client may retry. A
transaction-scoped advisory lock makes a concurrent duplicate fail fast with
409 IDEMPOTENCY_IN_PROGRESS instead of waiting on the unique index.
"""

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from lib_management.core.errors import Conflict
from lib_management.platform.models import IdempotencyRecord

MAX_KEY_LENGTH = 128


def payload_hash(payload: Any) -> str:
    canonical = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


@dataclass(frozen=True)
class Begin:
    record: IdempotencyRecord
    replay: bool

    @property
    def response_status(self) -> int:
        assert self.record.response_status is not None
        return self.record.response_status

    @property
    def response_body(self) -> Any:
        return self.record.response_body


def begin(
    session: Session,
    *,
    actor_id: uuid.UUID,
    operation: str,
    key: str,
    payload: Any,
    ttl: timedelta,
) -> Begin:
    if not 1 <= len(key) <= MAX_KEY_LENGTH:
        raise ValueError("Idempotency-Key must be 1-128 characters")
    digest = payload_hash(payload)
    scope = f"{actor_id}|{operation}|{key}"
    locked = session.execute(
        select(func.pg_try_advisory_xact_lock(func.hashtextextended(scope, 0)))
    ).scalar_one()
    if not locked:
        raise _in_progress()

    existing = session.execute(
        select(IdempotencyRecord).where(
            IdempotencyRecord.actor_id == actor_id,
            IdempotencyRecord.operation == operation,
            IdempotencyRecord.key == key,
        )
    ).scalar_one_or_none()
    now = datetime.now(UTC)
    if existing is not None and existing.expires_at <= now:
        session.execute(
            delete(IdempotencyRecord).where(IdempotencyRecord.id == existing.id)
        )
        existing = None
    if existing is not None:
        if existing.payload_hash != digest:
            raise Conflict(
                "Idempotency-Key đã dùng cho yêu cầu khác",
                code="IDEMPOTENCY_MISMATCH",
            )
        if existing.state == "COMPLETED":
            return Begin(existing, replay=True)
        raise _in_progress()

    created = IdempotencyRecord(
        actor_id=actor_id,
        operation=operation,
        key=key,
        payload_hash=digest,
        state="PENDING",
        expires_at=now + ttl,
    )
    session.add(created)
    session.flush()
    return Begin(created, replay=False)


def complete(session: Session, started: Begin, status_code: int, body: Any) -> None:
    """Stores the redacted response; commit happens with the business change."""
    started.record.state = "COMPLETED"
    started.record.response_status = status_code
    started.record.response_body = body
    session.flush()


def _in_progress() -> Conflict:
    return Conflict(
        "Yêu cầu cùng Idempotency-Key đang được xử lý",
        code="IDEMPOTENCY_IN_PROGRESS",
        headers={"Retry-After": "1"},
    )
