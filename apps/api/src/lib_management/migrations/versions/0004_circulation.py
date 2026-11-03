"""Policy, circulation and append-only finance tables; frozen PostgreSQL DDL."""

from alembic import op

revision = "0004_circulation"
down_revision = "0003_catalog_readers"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SEQUENCE policy_version_no_seq")
    op.execute(
        "\nCREATE TABLE policy_version (\n\tid UUID NOT NULL, \n\tversion_no INTEGER NOT NULL, \n\teffective_from TIMESTAMP WITH TIME ZONE NOT NULL, \n\teffective_to TIMESTAMP WITH TIME ZONE, \n\tstatus VARCHAR(16) NOT NULL, \n\trules JSONB NOT NULL, \n\trules_schema_version INTEGER NOT NULL, \n\tapproved_by UUID, \n\tapproved_at TIMESTAMP WITH TIME ZONE, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT pk_policy_version PRIMARY KEY (id), \n\tCONSTRAINT ck_policy_version_version_no_positive CHECK (version_no > 0), \n\tCONSTRAINT ck_policy_version_status CHECK (status IN ('DRAFT', 'ACTIVE', 'SUPERSEDED')), \n\tCONSTRAINT ex_policy_effective_range EXCLUDE USING gist (tstzrange(effective_from, effective_to, '[)') WITH &&) WHERE (status IN ('ACTIVE', 'SUPERSEDED')), \n\tCONSTRAINT ck_policy_version_effective_interval CHECK (effective_to IS NULL OR effective_to > effective_from), \n\tCONSTRAINT ck_policy_version_approval_state CHECK ((status = 'DRAFT' AND approved_by IS NULL AND approved_at IS NULL) OR (status IN ('ACTIVE','SUPERSEDED') AND approved_by IS NOT NULL AND approved_at IS NOT NULL)), \n\tCONSTRAINT uq_policy_version_version_no UNIQUE (version_no), \n\tCONSTRAINT fk_policy_version_approved_by_account FOREIGN KEY(approved_by) REFERENCES account (id)\n)\n\n"
    )
    op.execute(
        "CREATE INDEX ix_policy_version_created_id ON policy_version (created_at, id)"
    )
    op.execute(
        "\nCREATE TABLE loan (\n\tid UUID NOT NULL, \n\tloan_no VARCHAR(64) NOT NULL, \n\treader_id UUID NOT NULL, \n\tcard_id UUID NOT NULL, \n\tissued_by UUID NOT NULL, \n\tissued_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\trenewal_count INTEGER DEFAULT '0' NOT NULL, \n\tversion INTEGER DEFAULT '1' NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT pk_loan PRIMARY KEY (id), \n\tCONSTRAINT ck_loan_version_positive CHECK (version > 0), \n\tCONSTRAINT ck_loan_renewal_count CHECK (renewal_count >= 0), \n\tCONSTRAINT uq_loan_loan_no UNIQUE (loan_no), \n\tCONSTRAINT fk_loan_reader_id_reader FOREIGN KEY(reader_id) REFERENCES reader (id), \n\tCONSTRAINT fk_loan_card_id_reader_card FOREIGN KEY(card_id) REFERENCES reader_card (id), \n\tCONSTRAINT fk_loan_issued_by_account FOREIGN KEY(issued_by) REFERENCES account (id)\n)\n\n"
    )
    op.execute("CREATE INDEX ix_loan_created_id ON loan (created_at, id)")
    op.execute("CREATE INDEX ix_loan_reader_id ON loan (reader_id)")
    op.execute(
        "\nCREATE TABLE loan_item (\n\tid UUID NOT NULL, \n\tloan_id UUID NOT NULL, \n\tcopy_id UUID NOT NULL, \n\tissued_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tdue_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tclosed_at TIMESTAMP WITH TIME ZONE, \n\tclosure_reason VARCHAR(16), \n\tpolicy_version_id UUID NOT NULL, \n\tapplied_rules JSONB NOT NULL, \n\tversion INTEGER DEFAULT '1' NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT pk_loan_item PRIMARY KEY (id), \n\tCONSTRAINT ck_loan_item_version_positive CHECK (version > 0), \n\tCONSTRAINT ck_loan_item_due_after_issue CHECK (due_at > issued_at), \n\tCONSTRAINT ck_loan_item_closure_state CHECK ((closed_at IS NULL AND closure_reason IS NULL) OR (closed_at IS NOT NULL AND closure_reason IN ('RETURNED','LOST','VOIDED'))), \n\tCONSTRAINT fk_loan_item_loan_id_loan FOREIGN KEY(loan_id) REFERENCES loan (id), \n\tCONSTRAINT fk_loan_item_copy_id_book_copy FOREIGN KEY(copy_id) REFERENCES book_copy (id), \n\tCONSTRAINT fk_loan_item_policy_version_id_policy_version FOREIGN KEY(policy_version_id) REFERENCES policy_version (id)\n)\n\n"
    )
    op.execute("CREATE INDEX ix_loan_item_created_id ON loan_item (created_at, id)")
    op.execute(
        "CREATE INDEX ix_loan_item_due_open ON loan_item (due_at, id) WHERE closed_at IS NULL"
    )
    op.execute("CREATE INDEX ix_loan_item_loan_id ON loan_item (loan_id)")
    op.execute(
        "CREATE UNIQUE INDEX uq_loan_item_open_copy ON loan_item (copy_id) WHERE closed_at IS NULL"
    )
    op.execute(
        "\nCREATE TABLE renewal_event (\n\tid UUID NOT NULL, \n\tloan_id UUID NOT NULL, \n\tsequence_no INTEGER NOT NULL, \n\tactor_id UUID NOT NULL, \n\trenewed_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tpolicy_version_id UUID NOT NULL, \n\trequest_id VARCHAR(100) NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT pk_renewal_event PRIMARY KEY (id), \n\tCONSTRAINT uq_renewal_event_loan_id_sequence_no UNIQUE (loan_id, sequence_no), \n\tCONSTRAINT ck_renewal_event_sequence_positive CHECK (sequence_no > 0), \n\tCONSTRAINT fk_renewal_event_loan_id_loan FOREIGN KEY(loan_id) REFERENCES loan (id), \n\tCONSTRAINT fk_renewal_event_actor_id_account FOREIGN KEY(actor_id) REFERENCES account (id), \n\tCONSTRAINT fk_renewal_event_policy_version_id_policy_version FOREIGN KEY(policy_version_id) REFERENCES policy_version (id)\n)\n\n"
    )
    op.execute(
        "CREATE INDEX ix_renewal_event_created_id ON renewal_event (created_at, id)"
    )
    op.execute("CREATE INDEX ix_renewal_event_loan_id ON renewal_event (loan_id)")
    op.execute(
        "\nCREATE TABLE renewal_item (\n\trenewal_event_id UUID NOT NULL, \n\tloan_item_id UUID NOT NULL, \n\told_due_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tnew_due_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tapplied_rules JSONB NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT pk_renewal_item PRIMARY KEY (renewal_event_id, loan_item_id), \n\tCONSTRAINT ck_renewal_item_due_increases CHECK (new_due_at > old_due_at), \n\tCONSTRAINT fk_renewal_item_renewal_event_id_renewal_event FOREIGN KEY(renewal_event_id) REFERENCES renewal_event (id), \n\tCONSTRAINT fk_renewal_item_loan_item_id_loan_item FOREIGN KEY(loan_item_id) REFERENCES loan_item (id)\n)\n\n"
    )
    op.execute(
        "CREATE INDEX ix_renewal_item_loan_item_id ON renewal_item (loan_item_id)"
    )
    op.execute(
        "\nCREATE TABLE return_event (\n\tid UUID NOT NULL, \n\tloan_item_id UUID NOT NULL, \n\treturn_kind VARCHAR(16) NOT NULL, \n\tcondition VARCHAR(16), \n\treturned_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tprocessed_by UUID NOT NULL, \n\tnotes TEXT, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT pk_return_event PRIMARY KEY (id), \n\tCONSTRAINT ck_return_event_kind_condition CHECK ((return_kind = 'RETURNED' AND condition IS NOT NULL AND condition IN ('GOOD','DAMAGED')) OR (return_kind IN ('LOST','VOIDED') AND condition IS NULL)), \n\tCONSTRAINT fk_return_event_loan_item_id_loan_item FOREIGN KEY(loan_item_id) REFERENCES loan_item (id), \n\tCONSTRAINT fk_return_event_processed_by_account FOREIGN KEY(processed_by) REFERENCES account (id)\n)\n\n"
    )
    op.execute(
        "CREATE INDEX ix_return_event_created_id ON return_event (created_at, id)"
    )
    op.execute(
        "CREATE UNIQUE INDEX ix_return_event_loan_item_id ON return_event (loan_item_id)"
    )
    op.execute(
        "\nCREATE TABLE reservation (\n\tid UUID NOT NULL, \n\treader_id UUID NOT NULL, \n\tedition_id UUID NOT NULL, \n\tcopy_id UUID, \n\tfulfilled_loan_item_id UUID, \n\tstatus VARCHAR(16) NOT NULL, \n\tready_at TIMESTAMP WITH TIME ZONE, \n\tready_expires_at TIMESTAMP WITH TIME ZONE, \n\tcancellation_reason TEXT, \n\tpolicy_version_id UUID NOT NULL, \n\tapplied_rules JSONB NOT NULL, \n\tversion INTEGER DEFAULT '1' NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT pk_reservation PRIMARY KEY (id), \n\tCONSTRAINT ck_reservation_status CHECK (status IN ('QUEUED', 'READY', 'FULFILLED', 'CANCELLED', 'EXPIRED')), \n\tCONSTRAINT ck_reservation_version_positive CHECK (version > 0), \n\tCONSTRAINT ck_reservation_ready_state CHECK (status != 'READY' OR (copy_id IS NOT NULL AND ready_at IS NOT NULL AND ready_expires_at IS NOT NULL AND ready_expires_at > ready_at)), \n\tCONSTRAINT fk_reservation_reader_id_reader FOREIGN KEY(reader_id) REFERENCES reader (id), \n\tCONSTRAINT fk_reservation_edition_id_book_edition FOREIGN KEY(edition_id) REFERENCES book_edition (id), \n\tCONSTRAINT fk_reservation_copy_id_book_copy FOREIGN KEY(copy_id) REFERENCES book_copy (id), \n\tCONSTRAINT uq_reservation_fulfilled_loan_item_id UNIQUE (fulfilled_loan_item_id), \n\tCONSTRAINT fk_reservation_fulfilled_loan_item_id_loan_item FOREIGN KEY(fulfilled_loan_item_id) REFERENCES loan_item (id), \n\tCONSTRAINT fk_reservation_policy_version_id_policy_version FOREIGN KEY(policy_version_id) REFERENCES policy_version (id)\n)\n\n"
    )
    op.execute("CREATE INDEX ix_reservation_created_id ON reservation (created_at, id)")
    op.execute("CREATE INDEX ix_reservation_edition_id ON reservation (edition_id)")
    op.execute("CREATE INDEX ix_reservation_reader_id ON reservation (reader_id)")
    op.execute(
        "CREATE UNIQUE INDEX uq_reservation_active_reader_edition ON reservation (reader_id, edition_id) WHERE status IN ('QUEUED', 'READY')"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_reservation_ready_copy ON reservation (copy_id) WHERE status = 'READY'"
    )
    op.execute(
        "\nCREATE TABLE fine_charge (\n\tid UUID NOT NULL, \n\treader_id UUID NOT NULL, \n\tloan_item_id UUID, \n\tpolicy_version_id UUID NOT NULL, \n\treason VARCHAR(16) NOT NULL, \n\tassessed_amount NUMERIC(14, 0) NOT NULL, \n\tlate_days INTEGER, \n\tunit_rate NUMERIC(14, 0), \n\tcalculation JSONB NOT NULL, \n\tmanual_reason TEXT, \n\tassessed_by UUID NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT pk_fine_charge PRIMARY KEY (id), \n\tCONSTRAINT ck_fine_charge_assessed_amount_positive CHECK (assessed_amount > 0), \n\tCONSTRAINT ck_fine_charge_reason CHECK (reason IN ('LATE','DAMAGE','LOST','MANUAL')), \n\tCONSTRAINT ck_fine_charge_late_days CHECK (late_days IS NULL OR late_days >= 0), \n\tCONSTRAINT fk_fine_charge_reader_id_reader FOREIGN KEY(reader_id) REFERENCES reader (id), \n\tCONSTRAINT fk_fine_charge_loan_item_id_loan_item FOREIGN KEY(loan_item_id) REFERENCES loan_item (id), \n\tCONSTRAINT fk_fine_charge_policy_version_id_policy_version FOREIGN KEY(policy_version_id) REFERENCES policy_version (id), \n\tCONSTRAINT fk_fine_charge_assessed_by_account FOREIGN KEY(assessed_by) REFERENCES account (id)\n)\n\n"
    )
    op.execute("CREATE INDEX ix_fine_charge_created_id ON fine_charge (created_at, id)")
    op.execute("CREATE INDEX ix_fine_charge_loan_item_id ON fine_charge (loan_item_id)")
    op.execute("CREATE INDEX ix_fine_charge_reader_id ON fine_charge (reader_id)")
    op.execute(
        "\nCREATE TABLE payment (\n\tid UUID NOT NULL, \n\treader_id UUID NOT NULL, \n\treceipt_no VARCHAR(64) NOT NULL, \n\tamount NUMERIC(14, 0) NOT NULL, \n\tmethod VARCHAR(24) NOT NULL, \n\treceived_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\treceived_by UUID NOT NULL, \n\treference TEXT, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT pk_payment PRIMARY KEY (id), \n\tCONSTRAINT ck_payment_amount_positive CHECK (amount > 0), \n\tCONSTRAINT ck_payment_method CHECK (method IN ('CASH','TRANSFER_RECORD')), \n\tCONSTRAINT fk_payment_reader_id_reader FOREIGN KEY(reader_id) REFERENCES reader (id), \n\tCONSTRAINT uq_payment_receipt_no UNIQUE (receipt_no), \n\tCONSTRAINT fk_payment_received_by_account FOREIGN KEY(received_by) REFERENCES account (id)\n)\n\n"
    )
    op.execute("CREATE INDEX ix_payment_created_id ON payment (created_at, id)")
    op.execute("CREATE INDEX ix_payment_reader_id ON payment (reader_id)")
    op.execute(
        "\nCREATE TABLE payment_allocation (\n\tpayment_id UUID NOT NULL, \n\tcharge_id UUID NOT NULL, \n\tamount NUMERIC(14, 0) NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT pk_payment_allocation PRIMARY KEY (payment_id, charge_id), \n\tCONSTRAINT ck_payment_allocation_amount_positive CHECK (amount > 0), \n\tCONSTRAINT fk_payment_allocation_payment_id_payment FOREIGN KEY(payment_id) REFERENCES payment (id), \n\tCONSTRAINT fk_payment_allocation_charge_id_fine_charge FOREIGN KEY(charge_id) REFERENCES fine_charge (id)\n)\n\n"
    )
    op.execute(
        "CREATE INDEX ix_payment_allocation_charge_id ON payment_allocation (charge_id)"
    )
    op.execute(
        "CREATE INDEX ix_payment_allocation_payment_id ON payment_allocation (payment_id)"
    )
    op.execute(
        "\nCREATE TABLE waiver (\n\tid UUID NOT NULL, \n\tcharge_id UUID NOT NULL, \n\tamount NUMERIC(14, 0) NOT NULL, \n\tapproved_by UUID NOT NULL, \n\treason TEXT NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT pk_waiver PRIMARY KEY (id), \n\tCONSTRAINT ck_waiver_amount_positive CHECK (amount > 0), \n\tCONSTRAINT ck_waiver_reason CHECK (length(trim(reason)) > 0), \n\tCONSTRAINT fk_waiver_charge_id_fine_charge FOREIGN KEY(charge_id) REFERENCES fine_charge (id), \n\tCONSTRAINT fk_waiver_approved_by_account FOREIGN KEY(approved_by) REFERENCES account (id)\n)\n\n"
    )
    op.execute("CREATE INDEX ix_waiver_charge_id ON waiver (charge_id)")
    op.execute("CREATE INDEX ix_waiver_created_id ON waiver (created_at, id)")
    op.execute(
        "\nCREATE TABLE payment_reversal (\n\tid UUID NOT NULL, \n\tpayment_id UUID NOT NULL, \n\tamount NUMERIC(14, 0) NOT NULL, \n\tactor_id UUID NOT NULL, \n\treason TEXT NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT pk_payment_reversal PRIMARY KEY (id), \n\tCONSTRAINT ck_payment_reversal_amount_positive CHECK (amount > 0), \n\tCONSTRAINT fk_payment_reversal_payment_id_payment FOREIGN KEY(payment_id) REFERENCES payment (id), \n\tCONSTRAINT fk_payment_reversal_actor_id_account FOREIGN KEY(actor_id) REFERENCES account (id)\n)\n\n"
    )
    op.execute(
        "CREATE INDEX ix_payment_reversal_created_id ON payment_reversal (created_at, id)"
    )
    op.execute(
        "CREATE INDEX ix_payment_reversal_payment_id ON payment_reversal (payment_id)"
    )
    op.execute(
        "\nCREATE TABLE allocation_reversal (\n\tid UUID NOT NULL, \n\tpayment_id UUID NOT NULL, \n\tcharge_id UUID NOT NULL, \n\tamount NUMERIC(14, 0) NOT NULL, \n\tactor_id UUID NOT NULL, \n\treason TEXT NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT pk_allocation_reversal PRIMARY KEY (id), \n\tCONSTRAINT ck_allocation_reversal_amount_positive CHECK (amount > 0), \n\tCONSTRAINT fk_allocation_reversal_payment_id_payment_allocation FOREIGN KEY(payment_id, charge_id) REFERENCES payment_allocation (payment_id, charge_id), \n\tCONSTRAINT fk_allocation_reversal_payment_id_payment FOREIGN KEY(payment_id) REFERENCES payment (id), \n\tCONSTRAINT fk_allocation_reversal_charge_id_fine_charge FOREIGN KEY(charge_id) REFERENCES fine_charge (id), \n\tCONSTRAINT fk_allocation_reversal_actor_id_account FOREIGN KEY(actor_id) REFERENCES account (id)\n)\n\n"
    )
    op.execute(
        "CREATE INDEX ix_allocation_reversal_charge_id ON allocation_reversal (charge_id)"
    )
    op.execute(
        "CREATE INDEX ix_allocation_reversal_created_id ON allocation_reversal (created_at, id)"
    )
    op.execute(
        "CREATE INDEX ix_allocation_reversal_payment_id ON allocation_reversal (payment_id)"
    )
    op.execute(
        "\nCREATE TABLE waiver_reversal (\n\tid UUID NOT NULL, \n\twaiver_id UUID NOT NULL, \n\tamount NUMERIC(14, 0) NOT NULL, \n\tactor_id UUID NOT NULL, \n\treason TEXT NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT pk_waiver_reversal PRIMARY KEY (id), \n\tCONSTRAINT ck_waiver_reversal_amount_positive CHECK (amount > 0), \n\tCONSTRAINT fk_waiver_reversal_waiver_id_waiver FOREIGN KEY(waiver_id) REFERENCES waiver (id), \n\tCONSTRAINT fk_waiver_reversal_actor_id_account FOREIGN KEY(actor_id) REFERENCES account (id)\n)\n\n"
    )
    op.execute(
        "CREATE INDEX ix_waiver_reversal_created_id ON waiver_reversal (created_at, id)"
    )
    op.execute(
        "\nCREATE TABLE charge_assessment (\n\tid UUID NOT NULL, \n\treader_id UUID NOT NULL, \n\treturn_event_id UUID NOT NULL, \n\tkind VARCHAR(16) NOT NULL, \n\tproposed_amount NUMERIC(14, 0) NOT NULL, \n\treason TEXT NOT NULL, \n\tproposed_by UUID NOT NULL, \n\tstatus VARCHAR(24) NOT NULL, \n\tapproved_amount NUMERIC(14, 0), \n\tdecided_by UUID, \n\tdecided_at TIMESTAMP WITH TIME ZONE, \n\tdecision_reason TEXT, \n\tfine_charge_id UUID, \n\tversion INTEGER DEFAULT '1' NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT pk_charge_assessment PRIMARY KEY (id), \n\tCONSTRAINT uq_charge_assessment_return_event_id_kind UNIQUE (return_event_id, kind), \n\tCONSTRAINT ck_charge_assessment_kind CHECK (kind IN ('DAMAGE','LOST')), \n\tCONSTRAINT ck_charge_assessment_status CHECK (status IN ('PENDING','ASSESSED','CLOSED_NO_CHARGE')), \n\tCONSTRAINT ck_charge_assessment_proposed_amount CHECK (proposed_amount >= 0), \n\tCONSTRAINT ck_charge_assessment_version_positive CHECK (version > 0), \n\tCONSTRAINT ck_charge_assessment_decision_state CHECK ((status = 'PENDING' AND approved_amount IS NULL AND decided_by IS NULL AND decided_at IS NULL AND decision_reason IS NULL AND fine_charge_id IS NULL) OR (status = 'ASSESSED' AND approved_amount > 0 AND decided_by IS NOT NULL AND decided_at IS NOT NULL AND decision_reason IS NOT NULL AND length(trim(decision_reason)) > 0 AND fine_charge_id IS NOT NULL) OR (status = 'CLOSED_NO_CHARGE' AND approved_amount = 0 AND decided_by IS NOT NULL AND decided_at IS NOT NULL AND decision_reason IS NOT NULL AND length(trim(decision_reason)) > 0 AND fine_charge_id IS NULL)), \n\tCONSTRAINT fk_charge_assessment_reader_id_reader FOREIGN KEY(reader_id) REFERENCES reader (id), \n\tCONSTRAINT fk_charge_assessment_return_event_id_return_event FOREIGN KEY(return_event_id) REFERENCES return_event (id), \n\tCONSTRAINT fk_charge_assessment_proposed_by_account FOREIGN KEY(proposed_by) REFERENCES account (id), \n\tCONSTRAINT fk_charge_assessment_decided_by_account FOREIGN KEY(decided_by) REFERENCES account (id), \n\tCONSTRAINT uq_charge_assessment_fine_charge_id UNIQUE (fine_charge_id), \n\tCONSTRAINT fk_charge_assessment_fine_charge_id_fine_charge FOREIGN KEY(fine_charge_id) REFERENCES fine_charge (id)\n)\n\n"
    )
    op.execute(
        "CREATE INDEX ix_charge_assessment_reader_status ON charge_assessment (reader_id, status)"
    )
    op.create_foreign_key(
        "fk_reader_card_policy_version_id_policy_version",
        "reader_card",
        "policy_version",
        ["policy_version_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_reader_card_policy_version_id_policy_version",
        "reader_card",
        type_="foreignkey",
    )
    op.drop_table("charge_assessment")
    op.drop_table("waiver_reversal")
    op.drop_table("allocation_reversal")
    op.drop_table("payment_reversal")
    op.drop_table("waiver")
    op.drop_table("payment_allocation")
    op.drop_table("payment")
    op.drop_table("fine_charge")
    op.drop_table("reservation")
    op.drop_table("return_event")
    op.drop_table("renewal_item")
    op.drop_table("renewal_event")
    op.drop_table("loan_item")
    op.drop_table("loan")
    op.drop_table("policy_version")
    op.execute("DROP SEQUENCE policy_version_no_seq")
