"""Frozen report metadata and private artifact schema."""

from alembic import op

revision = "0005_reporting"
down_revision = "0004_circulation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE TABLE media_asset (\n"
        "\tid UUID NOT NULL, \n"
        "\tedition_id UUID, \n"
        "\tobject_key TEXT NOT NULL, \n"
        "\tmime_type VARCHAR(100) NOT NULL, \n"
        "\tbyte_size BIGINT NOT NULL, \n"
        "\tsha256 CHAR(64) NOT NULL, \n"
        "\tvisibility VARCHAR(16) NOT NULL, \n"
        "\tstatus VARCHAR(16) NOT NULL, \n"
        "\tuploaded_by UUID NOT NULL, \n"
        "\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n"
        "\tCONSTRAINT pk_media_asset PRIMARY KEY (id), \n"
        "\tCONSTRAINT ck_media_asset_byte_size_positive CHECK (byte_size >"
        " 0), \n"
        "\tCONSTRAINT ck_media_asset_visibility CHECK (visibility IN ('PUB"
        "LIC','PRIVATE')), \n"
        "\tCONSTRAINT ck_media_asset_status CHECK (status IN ('PENDING','R"
        "EADY','REJECTED','DELETED')), \n"
        "\tCONSTRAINT fk_media_asset_edition_id_book_edition FOREIGN KEY(e"
        "dition_id) REFERENCES book_edition (id), \n"
        "\tCONSTRAINT uq_media_asset_object_key UNIQUE (object_key), \n"
        "\tCONSTRAINT fk_media_asset_uploaded_by_account FOREIGN KEY(uploa"
        "ded_by) REFERENCES account (id)\n"
        ")"
    )
    op.execute(
        "CREATE TABLE report_job (\n"
        "\tid UUID NOT NULL, \n"
        "\tjob_id UUID NOT NULL, \n"
        "\trequested_by UUID NOT NULL, \n"
        "\treport_type VARCHAR(64) NOT NULL, \n"
        "\tfilter_snapshot JSONB NOT NULL, \n"
        "\tas_of TIMESTAMP WITH TIME ZONE NOT NULL, \n"
        "\tartifact_id UUID, \n"
        "\texpires_at TIMESTAMP WITH TIME ZONE, \n"
        "\trow_count BIGINT, \n"
        "\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n"
        "\tCONSTRAINT pk_report_job PRIMARY KEY (id), \n"
        "\tCONSTRAINT ck_report_job_row_count_non_negative CHECK (row_coun"
        "t >= 0), \n"
        "\tCONSTRAINT uq_report_job_job_id UNIQUE (job_id), \n"
        "\tCONSTRAINT fk_report_job_job_id_job FOREIGN KEY(job_id) REFEREN"
        "CES job (id), \n"
        "\tCONSTRAINT fk_report_job_requested_by_account FOREIGN KEY(reque"
        "sted_by) REFERENCES account (id), \n"
        "\tCONSTRAINT fk_report_job_artifact_id_media_asset FOREIGN KEY(ar"
        "tifact_id) REFERENCES media_asset (id)\n"
        ")"
    )
    op.execute(
        "CREATE INDEX ix_report_job_requested_by_created_at ON report_job (requested_by, created_at)"
    )


def downgrade() -> None:
    op.drop_table("report_job")
    op.drop_table("media_asset")
