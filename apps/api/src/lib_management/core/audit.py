"""Append-only audit trail written inside the command's Unit of Work."""

import uuid
from typing import Any, Literal

from sqlalchemy.orm import Session

from lib_management.core.request_id import current_request_id
from lib_management.platform.models import AuditLog

ActorType = Literal["USER", "SYSTEM", "ANONYMOUS"]
Outcome = Literal["SUCCESS", "DENIED", "FAILED"]


def record(
    session: Session,
    *,
    action: str,
    target_type: str,
    outcome: Outcome,
    actor_id: uuid.UUID | None = None,
    actor_type: ActorType = "USER",
    target_id: uuid.UUID | None = None,
    permission_code: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    """Adds an audit row; ``metadata`` must already be redacted by the caller."""
    if actor_id is None and actor_type == "USER":
        raise ValueError("USER audit entries require actor_id")
    entry = AuditLog(
        actor_id=actor_id,
        actor_type=actor_type,
        action=action,
        permission_code=permission_code,
        target_type=target_type,
        target_id=target_id,
        request_id=current_request_id() or "system",
        outcome=outcome,
        metadata_=metadata or {},
    )
    session.add(entry)
    return entry
