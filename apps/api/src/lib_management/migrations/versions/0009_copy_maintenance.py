"""Copy status MAINTENANCE ("Bảo trì", YC#2 / decision D1)."""

from alembic import op

revision = "0009_copy_maintenance"
down_revision = "0008_category_rules"
branch_labels = None
depends_on = None

OLD = "('AVAILABLE','ON_LOAN','HELD','REPAIR','LOST','RETIRED')"
NEW = "('AVAILABLE','ON_LOAN','HELD','REPAIR','MAINTENANCE','LOST','RETIRED')"


def upgrade() -> None:
    op.execute("ALTER TABLE book_copy DROP CONSTRAINT ck_book_copy_status")
    op.execute(
        f"ALTER TABLE book_copy ADD CONSTRAINT ck_book_copy_status CHECK (status IN {NEW})"
    )


def downgrade() -> None:
    # Copies in maintenance count as under repair in the older domain.
    op.execute("UPDATE book_copy SET status = 'REPAIR' WHERE status = 'MAINTENANCE'")
    op.execute("ALTER TABLE book_copy DROP CONSTRAINT ck_book_copy_status")
    op.execute(
        f"ALTER TABLE book_copy ADD CONSTRAINT ck_book_copy_status CHECK (status IN {OLD})"
    )
