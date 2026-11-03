"""Platform tables: audit_log, idempotency_record, outbox_event, job.

Revision ID: 0002_platform
Revises: 0001_identity
Create Date: 2026-11-03
"""

from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_platform"
down_revision: str | None = "0001_identity"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _created_at() -> sa.Column[Any]:
    return sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )


def upgrade() -> None:
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("actor_type", sa.String(16), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("permission_code", sa.String(100), nullable=True),
        sa.Column("target_type", sa.String(64), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=True),
        sa.Column("request_id", sa.String(100), nullable=False),
        sa.Column("outcome", sa.String(16), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=False),
        _created_at(),
        sa.PrimaryKeyConstraint("id", name="pk_audit_log"),
        sa.ForeignKeyConstraint(
            ["actor_id"], ["account.id"], name="fk_audit_log_actor_id_account"
        ),
        sa.CheckConstraint(
            "actor_type IN ('USER', 'SYSTEM', 'ANONYMOUS')",
            name="ck_audit_log_actor_type",
        ),
        sa.CheckConstraint(
            "outcome IN ('SUCCESS', 'DENIED', 'FAILED')", name="ck_audit_log_outcome"
        ),
    )
    op.create_index(
        "ix_audit_log_target_type_target_id_created_at",
        "audit_log",
        ["target_type", "target_id", "created_at"],
    )
    op.create_table(
        "idempotency_record",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("operation", sa.String(64), nullable=False),
        sa.Column("key", sa.String(128), nullable=False),
        sa.Column("payload_hash", sa.CHAR(64), nullable=False),
        sa.Column("response_status", sa.SmallInteger(), nullable=True),
        sa.Column("response_body", postgresql.JSONB(), nullable=True),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        _created_at(),
        sa.PrimaryKeyConstraint("id", name="pk_idempotency_record"),
        sa.ForeignKeyConstraint(
            ["actor_id"], ["account.id"], name="fk_idempotency_record_actor_id_account"
        ),
        sa.UniqueConstraint(
            "actor_id",
            "operation",
            "key",
            name="uq_idempotency_record_actor_id_operation_key",
        ),
        sa.CheckConstraint(
            "state IN ('PENDING', 'COMPLETED')", name="ck_idempotency_record_state"
        ),
    )
    op.create_table(
        "outbox_event",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("aggregate_type", sa.String(64), nullable=False),
        sa.Column("aggregate_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        _created_at(),
        sa.PrimaryKeyConstraint("id", name="pk_outbox_event"),
    )
    op.create_index(
        "ix_outbox_event_unprocessed",
        "outbox_event",
        ["created_at", "id"],
        postgresql_where=sa.text("processed_at IS NULL"),
    )
    op.create_table(
        "job",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("outbox_event_id", sa.Uuid(), nullable=True),
        sa.Column("dedupe_key", sa.String(200), nullable=False),
        sa.Column("job_type", sa.String(64), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lease_owner", sa.String(100), nullable=True),
        sa.Column("lease_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_code", sa.String(100), nullable=True),
        _created_at(),
        sa.PrimaryKeyConstraint("id", name="pk_job"),
        sa.ForeignKeyConstraint(
            ["outbox_event_id"],
            ["outbox_event.id"],
            name="fk_job_outbox_event_id_outbox_event",
        ),
        sa.UniqueConstraint("dedupe_key", name="uq_job_dedupe_key"),
        sa.CheckConstraint(
            "status IN ('QUEUED', 'RUNNING', 'SUCCEEDED', 'FAILED', 'DEAD')",
            name="ck_job_status",
        ),
        sa.CheckConstraint("attempt >= 0", name="ck_job_attempt_non_negative"),
    )
    op.create_index(
        "ix_job_status_next_attempt_at_lease_until",
        "job",
        ["status", "next_attempt_at", "lease_until"],
    )


def downgrade() -> None:
    op.drop_index("ix_job_status_next_attempt_at_lease_until", table_name="job")
    op.drop_table("job")
    op.drop_index("ix_outbox_event_unprocessed", table_name="outbox_event")
    op.drop_table("outbox_event")
    op.drop_table("idempotency_record")
    op.drop_index(
        "ix_audit_log_target_type_target_id_created_at", table_name="audit_log"
    )
    op.drop_table("audit_log")
