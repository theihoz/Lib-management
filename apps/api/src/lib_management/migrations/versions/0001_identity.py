"""Identity tables: account, role, permission, account_role, role_permission.

account.reader_id is a nullable UNIQUE uuid without a foreign key: the reader
table belongs to BE04, whose first migration adds
FOREIGN KEY (reader_id) REFERENCES reader(id).

Revision ID: 0001_identity
Revises:
Create Date: 2026-11-03
"""

from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op

revision: str = "0001_identity"
down_revision: str | None = None
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
        "account",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("issuer", sa.Text(), nullable=False),
        sa.Column("subject", sa.Text(), nullable=False),
        sa.Column("reader_id", sa.Uuid(), nullable=True),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("auth_version", sa.Integer(), nullable=False, server_default="1"),
        _created_at(),
        sa.PrimaryKeyConstraint("id", name="pk_account"),
        sa.UniqueConstraint("issuer", "subject", name="uq_account_issuer_subject"),
        sa.UniqueConstraint("reader_id", name="uq_account_reader_id"),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'LOCKED', 'DISABLED')", name="ck_account_status"
        ),
    )
    op.create_table(
        "role",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        _created_at(),
        sa.PrimaryKeyConstraint("id", name="pk_role"),
        sa.UniqueConstraint("code", name="uq_role_code"),
    )
    op.create_table(
        "permission",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        _created_at(),
        sa.PrimaryKeyConstraint("id", name="pk_permission"),
        sa.UniqueConstraint("code", name="uq_permission_code"),
    )
    op.create_table(
        "account_role",
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("granted_by", sa.Uuid(), nullable=False),
        _created_at(),
        sa.PrimaryKeyConstraint("account_id", "role_id", name="pk_account_role"),
        sa.ForeignKeyConstraint(
            ["account_id"], ["account.id"], name="fk_account_role_account_id_account"
        ),
        sa.ForeignKeyConstraint(
            ["role_id"], ["role.id"], name="fk_account_role_role_id_role"
        ),
        sa.ForeignKeyConstraint(
            ["granted_by"], ["account.id"], name="fk_account_role_granted_by_account"
        ),
    )
    op.create_table(
        "role_permission",
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("permission_id", sa.Uuid(), nullable=False),
        _created_at(),
        sa.PrimaryKeyConstraint("role_id", "permission_id", name="pk_role_permission"),
        sa.ForeignKeyConstraint(
            ["role_id"], ["role.id"], name="fk_role_permission_role_id_role"
        ),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["permission.id"],
            name="fk_role_permission_permission_id_permission",
        ),
    )


def downgrade() -> None:
    op.drop_table("role_permission")
    op.drop_table("account_role")
    op.drop_table("permission")
    op.drop_table("role")
    op.drop_table("account")
