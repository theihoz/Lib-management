"""Phase 2 schema: acquisition, backup manifest, notifications and consent."""

from alembic import op

revision = "0006_phase2_schema"
down_revision = "0005_reporting"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE TABLE acquisition_receipt (\n\tid UUID NOT NULL, \n\treceipt_"
        "no VARCHAR(64) NOT NULL, \n\tsupplier VARCHAR(200) NOT NULL, \n\trec"
        "eived_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tstatus VARCHAR(16)"
        " NOT NULL, \n\tapproved_by UUID, \n\tcreated_at TIMESTAMP WITH TIME "
        "ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT pk_acquisition_receipt"
        " PRIMARY KEY (id), \n\tCONSTRAINT ck_acquisition_receipt_status CH"
        "ECK (status IN ('DRAFT','POSTED','CANCELLED')), \n\tCONSTRAINT ck_"
        "acquisition_receipt_posted_approved CHECK (status <> 'POSTED' OR"
        " approved_by IS NOT NULL), \n\tCONSTRAINT uq_acquisition_receipt_r"
        "eceipt_no UNIQUE (receipt_no), \n\tCONSTRAINT fk_acquisition_recei"
        "pt_approved_by_account FOREIGN KEY(approved_by) REFERENCES accou"
        "nt (id)\n)"
    )
    op.execute(
        "CREATE TABLE acquisition_receipt_item (\n\tid UUID NOT NULL, \n\trec"
        "eipt_id UUID NOT NULL, \n\tedition_id UUID NOT NULL, \n\tquantity IN"
        "TEGER NOT NULL, \n\tunit_price NUMERIC(14, 0) NOT NULL, \n\tcreated_"
        "at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT"
        " pk_acquisition_receipt_item PRIMARY KEY (id), \n\tCONSTRAINT ck_a"
        "cquisition_receipt_item_quantity_positive CHECK (quantity > 0), "
        "\n\tCONSTRAINT ck_acquisition_receipt_item_unit_price_non_negative"
        " CHECK (unit_price >= 0), \n\tCONSTRAINT fk_acquisition_receipt_it"
        "em_receipt_id_acquisition_receipt FOREIGN KEY(receipt_id) REFERE"
        "NCES acquisition_receipt (id), \n\tCONSTRAINT fk_acquisition_recei"
        "pt_item_edition_id_book_edition FOREIGN KEY(edition_id) REFERENC"
        "ES book_edition (id)\n)"
    )
    op.execute(
        "CREATE INDEX ix_acquisition_receipt_item_receipt_id ON acquisiti"
        "on_receipt_item (receipt_id)"
    )
    op.execute(
        "CREATE TABLE backup_manifest (\n\tid UUID NOT NULL, \n\tschema_versi"
        "on VARCHAR(64) NOT NULL, \n\tsnapshot_at TIMESTAMP WITH TIME ZONE "
        "NOT NULL, \n\tencrypted_object_key TEXT NOT NULL, \n\tsha256 CHAR(64"
        ") NOT NULL, \n\tverified_at TIMESTAMP WITH TIME ZONE, \n\trestore_dr"
        "ill_result JSONB, \n\tcreated_by UUID, \n\tcreated_at TIMESTAMP WITH"
        " TIME ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT pk_backup_manife"
        "st PRIMARY KEY (id), \n\tCONSTRAINT uq_backup_manifest_encrypted_o"
        "bject_key UNIQUE (encrypted_object_key), \n\tCONSTRAINT fk_backup_"
        "manifest_created_by_account FOREIGN KEY(created_by) REFERENCES a"
        "ccount (id)\n)"
    )
    op.execute(
        "CREATE TABLE notification (\n\tid UUID NOT NULL, \n\tevent_id UUID, "
        "\n\treader_id UUID NOT NULL, \n\tkind VARCHAR(16) NOT NULL, \n\treserv"
        "ation_id UUID, \n\tsummary TEXT NOT NULL, \n\tread_at TIMESTAMP WITH"
        " TIME ZONE, \n\tdedupe_key VARCHAR(200) NOT NULL, \n\tcreated_at TIM"
        "ESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT pk_no"
        "tification PRIMARY KEY (id), \n\tCONSTRAINT ck_notification_kind C"
        "HECK (kind IN ('READY','OVERDUE')), \n\tCONSTRAINT ck_notification"
        "_ready_reservation CHECK (kind <> 'READY' OR reservation_id IS N"
        "OT NULL), \n\tCONSTRAINT fk_notification_event_id_outbox_event FOR"
        "EIGN KEY(event_id) REFERENCES outbox_event (id), \n\tCONSTRAINT fk"
        "_notification_reader_id_reader FOREIGN KEY(reader_id) REFERENCES"
        " reader (id), \n\tCONSTRAINT fk_notification_reservation_id_reserv"
        "ation FOREIGN KEY(reservation_id) REFERENCES reservation (id), \n"
        "\tCONSTRAINT uq_notification_dedupe_key UNIQUE (dedupe_key)\n)"
    )
    op.execute("CREATE INDEX ix_notification_reader_id ON notification (reader_id)")
    op.execute(
        "CREATE TABLE notification_delivery (\n\tid UUID NOT NULL, \n\tnotifi"
        "cation_id UUID NOT NULL, \n\tchannel VARCHAR(16) NOT NULL, \n\tstatu"
        "s VARCHAR(16) NOT NULL, \n\tjob_id UUID NOT NULL, \n\tprovider_messa"
        "ge_id TEXT, \n\tdelivered_at TIMESTAMP WITH TIME ZONE, \n\tlast_erro"
        "r_code TEXT, \n\tCONSTRAINT pk_notification_delivery PRIMARY KEY ("
        "id), \n\tCONSTRAINT uq_notification_delivery_notification_id_chann"
        "el UNIQUE (notification_id, channel), \n\tCONSTRAINT ck_notificati"
        "on_delivery_channel CHECK (channel IN ('EMAIL')), \n\tCONSTRAINT c"
        "k_notification_delivery_status CHECK (status IN ('QUEUED','SENDI"
        "NG','DELIVERED','FAILED','SKIPPED')), \n\tCONSTRAINT fk_notificati"
        "on_delivery_notification_id_notification FOREIGN KEY(notificatio"
        "n_id) REFERENCES notification (id), \n\tCONSTRAINT fk_notification"
        "_delivery_job_id_job FOREIGN KEY(job_id) REFERENCES job (id)\n)"
    )
    op.execute(
        "CREATE TABLE notification_preference (\n\treader_id UUID NOT NULL,"
        " \n\temail_consent BOOLEAN DEFAULT false NOT NULL, \n\tchanged_by UU"
        "ID NOT NULL, \n\tupdated_at TIMESTAMP WITH TIME ZONE DEFAULT now()"
        " NOT NULL, \n\tCONSTRAINT pk_notification_preference PRIMARY KEY ("
        "reader_id), \n\tCONSTRAINT fk_notification_preference_reader_id_re"
        "ader FOREIGN KEY(reader_id) REFERENCES reader (id), \n\tCONSTRAINT"
        " fk_notification_preference_changed_by_account FOREIGN KEY(chang"
        "ed_by) REFERENCES account (id)\n)"
    )


def downgrade() -> None:
    op.drop_table("notification_preference")
    op.drop_table("notification_delivery")
    op.drop_table("notification")
    op.drop_table("backup_manifest")
    op.drop_table("acquisition_receipt_item")
    op.drop_table("acquisition_receipt")
