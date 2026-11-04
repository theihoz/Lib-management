"""Manual fine proposals (YC#11 / decision D2): ChargeAssessment kind MANUAL."""

from alembic import op

revision = "0010_manual_assessment"
down_revision = "0009_copy_maintenance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE charge_assessment ALTER COLUMN return_event_id DROP NOT NULL"
    )
    op.execute(
        "ALTER TABLE charge_assessment ADD COLUMN loan_item_id UUID "
        "CONSTRAINT fk_charge_assessment_loan_item_id_loan_item "
        "REFERENCES loan_item (id)"
    )
    op.execute(
        "ALTER TABLE charge_assessment DROP CONSTRAINT ck_charge_assessment_kind"
    )
    op.execute(
        "ALTER TABLE charge_assessment ADD CONSTRAINT ck_charge_assessment_kind "
        "CHECK (kind IN ('DAMAGE','LOST','MANUAL'))"
    )
    op.execute(
        "ALTER TABLE charge_assessment ADD CONSTRAINT "
        "ck_charge_assessment_manual_source "
        "CHECK ((kind = 'MANUAL') = (return_event_id IS NULL))"
    )


def downgrade() -> None:
    op.execute("DELETE FROM charge_assessment WHERE kind = 'MANUAL'")
    op.execute(
        "ALTER TABLE charge_assessment DROP CONSTRAINT ck_charge_assessment_manual_source"
    )
    op.execute(
        "ALTER TABLE charge_assessment DROP CONSTRAINT ck_charge_assessment_kind"
    )
    op.execute(
        "ALTER TABLE charge_assessment ADD CONSTRAINT ck_charge_assessment_kind "
        "CHECK (kind IN ('DAMAGE','LOST'))"
    )
    op.execute("ALTER TABLE charge_assessment DROP COLUMN loan_item_id")
    op.execute(
        "ALTER TABLE charge_assessment ALTER COLUMN return_event_id SET NOT NULL"
    )
