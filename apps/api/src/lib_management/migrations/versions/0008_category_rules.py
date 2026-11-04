"""QĐ04 main categories A, B, C and QĐ09 unique category names.

A, B, C are inserted as protected roots; new categories must hang below them.
Roots created before this migration are kept (move their children under A/B/C
when convenient). The name index fails if two categories already share a name
ignoring case; rename one first.
"""

from alembic import op

revision = "0008_category_rules"
down_revision = "0007_reader_rules"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "INSERT INTO category (id, code, name, parent_id, is_root) VALUES "
        "(gen_random_uuid(), 'A', 'Thể loại A', NULL, true), "
        "(gen_random_uuid(), 'B', 'Thể loại B', NULL, true), "
        "(gen_random_uuid(), 'C', 'Thể loại C', NULL, true) "
        "ON CONFLICT (code) DO NOTHING"
    )
    op.execute(
        "UPDATE category SET is_root = true "
        "WHERE code IN ('A','B','C') AND parent_id IS NULL"
    )
    op.execute("CREATE UNIQUE INDEX uq_category_name_lower ON category (lower(name))")


def downgrade() -> None:
    op.execute("DROP INDEX uq_category_name_lower")
    # A/B/C stay: books may already be classified under them.
