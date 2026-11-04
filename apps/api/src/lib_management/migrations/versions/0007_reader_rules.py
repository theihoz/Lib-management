"""Reader rules from the spec: type X/Y/Z (BM02) and one reader per email (Lab 2).

The CHECK is added NOT VALID so databases holding older free-text types still
upgrade; every new or edited row is checked. Run
``ALTER TABLE reader VALIDATE CONSTRAINT ck_reader_reader_type`` after fixing them.
The email index fails if two readers already share an email (case-insensitive);
merge or correct those rows first.
"""

from alembic import op

revision = "0007_reader_rules"
down_revision = "0006_phase2_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE reader ADD CONSTRAINT ck_reader_reader_type "
        "CHECK (reader_type IN ('X','Y','Z')) NOT VALID"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_reader_email_lower ON reader (lower(email)) "
        "WHERE email IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX uq_reader_email_lower")
    op.execute("ALTER TABLE reader DROP CONSTRAINT ck_reader_reader_type")
