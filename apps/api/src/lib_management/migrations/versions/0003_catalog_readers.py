"""Normalized catalog and reader tables. Policy FK follows in 0004."""

from alembic import op

revision = "0003_catalog_readers"
down_revision = "0002_platform"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE TABLE publisher (\n\tid UUID NOT NULL, \n\tname VARCHAR(200) NOT NULL, \n\taddress TEXT, \n\tstatus VARCHAR(16) NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT pk_publisher PRIMARY KEY (id), \n\tCONSTRAINT ck_publisher_name CHECK (length(trim(name)) > 0), \n\tCONSTRAINT ck_publisher_status CHECK (status IN ('ACTIVE','INACTIVE'))\n)"
    )
    op.execute(
        "CREATE TABLE author (\n\tid UUID NOT NULL, \n\tname VARCHAR(200) NOT NULL, \n\tbiography TEXT, \n\tstatus VARCHAR(16) NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT pk_author PRIMARY KEY (id), \n\tCONSTRAINT ck_author_name CHECK (length(trim(name)) > 0), \n\tCONSTRAINT ck_author_status CHECK (status IN ('ACTIVE','INACTIVE'))\n)"
    )
    op.execute(
        "CREATE TABLE category (\n\tid UUID NOT NULL, \n\tcode VARCHAR(32) NOT NULL, \n\tname VARCHAR(120) NOT NULL, \n\tparent_id UUID, \n\tis_root BOOLEAN DEFAULT 'false' NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT pk_category PRIMARY KEY (id), \n\tCONSTRAINT uq_category_code UNIQUE (code), \n\tCONSTRAINT fk_category_parent_id_category FOREIGN KEY(parent_id) REFERENCES category (id)\n)"
    )
    op.execute(
        "CREATE TABLE book_edition (\n\tid UUID NOT NULL, \n\tisbn VARCHAR(13), \n\ttitle VARCHAR(300) NOT NULL, \n\tpublication_year SMALLINT NOT NULL, \n\tpublisher_id UUID, \n\tlanguage VARCHAR(32), \n\tdescription TEXT, \n\tstatus VARCHAR(16) NOT NULL, \n\tversion INTEGER DEFAULT '1' NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT pk_book_edition PRIMARY KEY (id), \n\tCONSTRAINT ck_book_edition_title CHECK (length(trim(title)) > 0), \n\tCONSTRAINT ck_book_edition_status CHECK (status IN ('ACTIVE','INACTIVE')), \n\tCONSTRAINT ck_book_edition_version CHECK (version > 0), \n\tCONSTRAINT uq_book_edition_isbn UNIQUE (isbn), \n\tCONSTRAINT fk_book_edition_publisher_id_publisher FOREIGN KEY(publisher_id) REFERENCES publisher (id)\n)"
    )
    op.execute(
        "CREATE TABLE book_author (\n\tedition_id UUID NOT NULL, \n\tauthor_id UUID NOT NULL, \n\tordinal SMALLINT NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT pk_book_author PRIMARY KEY (edition_id, author_id), \n\tCONSTRAINT uq_book_author_edition_id_ordinal UNIQUE (edition_id, ordinal), \n\tCONSTRAINT ck_book_author_ordinal CHECK (ordinal > 0), \n\tCONSTRAINT fk_book_author_edition_id_book_edition FOREIGN KEY(edition_id) REFERENCES book_edition (id), \n\tCONSTRAINT fk_book_author_author_id_author FOREIGN KEY(author_id) REFERENCES author (id)\n)"
    )
    op.execute(
        "CREATE TABLE book_category (\n\tedition_id UUID NOT NULL, \n\tcategory_id UUID NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT pk_book_category PRIMARY KEY (edition_id, category_id), \n\tCONSTRAINT fk_book_category_edition_id_book_edition FOREIGN KEY(edition_id) REFERENCES book_edition (id), \n\tCONSTRAINT fk_book_category_category_id_category FOREIGN KEY(category_id) REFERENCES category (id)\n)"
    )
    op.execute(
        "CREATE TABLE location (\n\tid UUID NOT NULL, \n\tcode VARCHAR(32) NOT NULL, \n\tname VARCHAR(120) NOT NULL, \n\tstatus VARCHAR(16) NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT pk_location PRIMARY KEY (id), \n\tCONSTRAINT ck_location_status CHECK (status IN ('ACTIVE','INACTIVE')), \n\tCONSTRAINT uq_location_code UNIQUE (code)\n)"
    )
    op.execute(
        "CREATE TABLE book_copy (\n\tid UUID NOT NULL, \n\tedition_id UUID NOT NULL, \n\tbarcode VARCHAR(64) NOT NULL, \n\tlocation_id UUID, \n\tstatus VARCHAR(16) NOT NULL, \n\tacquired_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tsource_receipt_item_id UUID, \n\tversion INTEGER DEFAULT '1' NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT pk_book_copy PRIMARY KEY (id), \n\tCONSTRAINT ck_book_copy_status CHECK (status IN ('AVAILABLE','ON_LOAN','HELD','REPAIR','LOST','RETIRED')), \n\tCONSTRAINT ck_book_copy_version CHECK (version > 0), \n\tCONSTRAINT fk_book_copy_edition_id_book_edition FOREIGN KEY(edition_id) REFERENCES book_edition (id), \n\tCONSTRAINT uq_book_copy_barcode UNIQUE (barcode), \n\tCONSTRAINT fk_book_copy_location_id_location FOREIGN KEY(location_id) REFERENCES location (id)\n)"
    )
    op.execute("CREATE INDEX ix_book_copy_edition_id ON book_copy (edition_id)")
    op.execute(
        "CREATE TABLE reader (\n\tid UUID NOT NULL, \n\treader_code VARCHAR(32) NOT NULL, \n\tfull_name VARCHAR(200) NOT NULL, \n\tbirth_date DATE NOT NULL, \n\treader_type VARCHAR(8) NOT NULL, \n\temail VARCHAR(254), \n\tphone VARCHAR(32), \n\taddress TEXT, \n\tstatus VARCHAR(16) NOT NULL, \n\tversion INTEGER DEFAULT '1' NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT pk_reader PRIMARY KEY (id), \n\tCONSTRAINT ck_reader_status CHECK (status IN ('ACTIVE','SUSPENDED','INACTIVE')), \n\tCONSTRAINT ck_reader_version CHECK (version > 0), \n\tCONSTRAINT uq_reader_reader_code UNIQUE (reader_code)\n)"
    )
    op.execute(
        "CREATE TABLE reader_card (\n\tid UUID NOT NULL, \n\treader_id UUID NOT NULL, \n\tcard_no VARCHAR(64) NOT NULL, \n\tissued_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\texpires_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tstatus VARCHAR(16) NOT NULL, \n\tissued_by UUID NOT NULL, \n\tpolicy_version_id UUID NOT NULL, \n\tversion INTEGER DEFAULT '1' NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tCONSTRAINT pk_reader_card PRIMARY KEY (id), \n\tCONSTRAINT ck_reader_card_status CHECK (status IN ('ACTIVE','BLOCKED','REVOKED')), \n\tCONSTRAINT ck_reader_card_validity CHECK (expires_at > issued_at), \n\tCONSTRAINT ck_reader_card_version CHECK (version > 0), \n\tCONSTRAINT fk_reader_card_reader_id_reader FOREIGN KEY(reader_id) REFERENCES reader (id), \n\tCONSTRAINT uq_reader_card_card_no UNIQUE (card_no), \n\tCONSTRAINT fk_reader_card_issued_by_account FOREIGN KEY(issued_by) REFERENCES account (id)\n)"
    )
    op.execute("CREATE INDEX ix_reader_card_reader_id ON reader_card (reader_id)")
    op.create_foreign_key(
        "fk_account_reader_id_reader", "account", "reader", ["reader_id"], ["id"]
    )


def downgrade() -> None:
    op.drop_constraint("fk_account_reader_id_reader", "account", type_="foreignkey")
    op.drop_table("reader_card")
    op.drop_table("reader")
    op.drop_table("book_copy")
    op.drop_table("location")
    op.drop_table("book_category")
    op.drop_table("book_author")
    op.drop_table("book_edition")
    op.drop_table("category")
    op.drop_table("author")
    op.drop_table("publisher")
