"""Local demo data (database-design.md: "seed dữ liệu demo riêng").

Operator command ``seed-demo``; never run against production. Idempotent: rows
are matched by their natural keys (codes, barcodes, card numbers) and only
missing ones are inserted, all in the caller's transaction.
"""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from lib_management.catalog.models import (
    Author,
    BookAuthor,
    BookCategory,
    BookCopy,
    BookEdition,
    Category,
    Location,
    Publisher,
)
from lib_management.circulation.models import PolicyVersion
from lib_management.circulation.service import RULES, RULES_SCHEMA_VERSION
from lib_management.identity import service
from lib_management.identity.models import Account
from lib_management.readers.models import Reader, ReaderCard
from lib_management.readers.service import add_calendar_months

SEED_ISSUER = "urn:lib-management:demo-seed"
SEED_SUBJECT = "demo-seed"

PUBLISHERS = (
    "NXB Trẻ",
    "NXB Kim Đồng",
    "NXB Giáo dục Việt Nam",
    "NXB Khoa học và Kỹ thuật",
)
# QĐ04: demo categories hang below the main categories A, B, C (migration 0008).
CATEGORIES = (
    ("VH", "Văn học", "A"),
    ("TN", "Thiếu nhi", "A"),
    ("CNTT", "Công nghệ thông tin", "B"),
    ("KT", "Kinh tế", "C"),
)
LOCATIONS = (("KHO-A", "Kho A — tầng 1"), ("KHO-B", "Kho B — tầng 2"))
# (title, year, publisher, author, category, language, copies)
EDITIONS = (
    ("Cho tôi xin một vé đi tuổi thơ", 2023, 0, "Nguyễn Nhật Ánh", "VH", "vi", 3),
    ("Mắt biếc", 2022, 0, "Nguyễn Nhật Ánh", "VH", "vi", 2),
    ("Dế Mèn phiêu lưu ký", 2021, 1, "Tô Hoài", "TN", "vi", 3),
    ("Truyện cổ tích Việt Nam", 2024, 1, "Nhiều tác giả", "TN", "vi", 2),
    ("Nhập môn cơ sở dữ liệu", 2023, 2, "Nguyễn Văn Minh", "CNTT", "vi", 2),
    ("Lập trình Python cơ bản", 2025, 3, "Trần Thị Lan", "CNTT", "vi", 3),
    ("Công nghệ phần mềm", 2024, 2, "Lê Quang Huy", "CNTT", "vi", 2),
    ("Kinh tế học vi mô", 2020, 2, "Phạm Thu Hà", "KT", "vi", 1),
)
# (code, name, birth date, type, email)
READERS = (
    ("DG0001", "Nguyễn Minh An", date(2004, 3, 12), "X", "an.nguyen@example.test"),
    ("DG0002", "Trần Thu Hà", date(1998, 9, 1), "Y", "ha.tran@example.test"),
    ("DG0003", "Lê Quốc Bảo", date(2008, 1, 20), "X", None),
    ("DG0004", "Phạm Gia Huy", date(1990, 6, 5), "Y", "huy.pham@example.test"),
    ("DG0005", "Võ Thanh Tâm", date(2002, 11, 30), "X", None),
)


@dataclass
class DemoReport:
    created: dict[str, int] = field(default_factory=dict)
    linked_reader: str | None = None

    def add(self, label: str) -> None:
        self.created[label] = self.created.get(label, 0) + 1


def _actor(session: Session) -> Account:
    """Owner of approvals and card issues; has no IdP login."""
    return service.bootstrap_account(
        session,
        issuer=SEED_ISSUER,
        subject=SEED_SUBJECT,
        display_name="Dữ liệu mẫu",
        role_codes=["LIBRARIAN"],
    )


def _by[T](session: Session, model: type[T], **keys: object) -> T | None:
    return session.scalar(select(model).filter_by(**keys))


def seed_demo(
    session: Session,
    *,
    link_issuer: str | None = None,
    link_subject: str | None = None,
) -> DemoReport:
    report = DemoReport()
    now = datetime.now(UTC)
    actor = _actor(session)

    if (
        session.scalar(select(PolicyVersion.id).where(PolicyVersion.status == "ACTIVE"))
        is None
    ):
        session.add(
            PolicyVersion(
                effective_from=now - timedelta(days=1),
                status="ACTIVE",
                rules=RULES,
                rules_schema_version=RULES_SCHEMA_VERSION,
                approved_by=actor.id,
                approved_at=now - timedelta(days=1),
            )
        )
        session.flush()
        report.add("policy_version")
    policy_id = session.scalar(
        select(PolicyVersion.id).where(PolicyVersion.status == "ACTIVE")
    )

    publishers = []
    for name in PUBLISHERS:
        publisher = _by(session, Publisher, name=name)
        if publisher is None:
            publisher = Publisher(name=name, status="ACTIVE")
            session.add(publisher)
            report.add("publisher")
        publishers.append(publisher)
    categories = {}
    for code, name, parent_code in CATEGORIES:
        category = _by(session, Category, code=code)
        if category is None:
            parent = _by(session, Category, code=parent_code)
            category = Category(
                code=code, name=name, parent_id=parent.id if parent else None
            )
            session.add(category)
            report.add("category")
        categories[code] = category
    locations = []
    for code, name in LOCATIONS:
        location = _by(session, Location, code=code)
        if location is None:
            location = Location(code=code, name=name, status="ACTIVE")
            session.add(location)
            report.add("location")
        locations.append(location)
    session.flush()

    barcode_no = 0
    for (
        title,
        year,
        publisher_no,
        author_name,
        category_code,
        language,
        copies,
    ) in EDITIONS:
        edition = _by(session, BookEdition, title=title)
        if edition is None:
            edition = BookEdition(
                title=title,
                publication_year=year,
                publisher_id=publishers[publisher_no].id,
                language=language,
                status="ACTIVE",
            )
            session.add(edition)
            author = _by(session, Author, name=author_name)
            if author is None:
                author = Author(name=author_name, status="ACTIVE")
                session.add(author)
                report.add("author")
            session.flush()
            session.add(
                BookAuthor(edition_id=edition.id, author_id=author.id, ordinal=1)
            )
            session.add(
                BookCategory(
                    edition_id=edition.id,
                    category_id=categories[category_code].id,
                )
            )
            report.add("book_edition")
        for _ in range(copies):
            barcode_no += 1
            barcode = f"DEMO-{barcode_no:04d}"
            if _by(session, BookCopy, barcode=barcode) is None:
                session.add(
                    BookCopy(
                        edition_id=edition.id,
                        barcode=barcode,
                        location_id=locations[barcode_no % len(locations)].id,
                        status="AVAILABLE",
                        acquired_at=now - timedelta(days=30),
                    )
                )
                report.add("book_copy")
    session.flush()

    first_reader: uuid.UUID | None = None
    for code, name, birth_date, reader_type, email in READERS:
        reader = _by(session, Reader, reader_code=code)
        if reader is None:
            reader = Reader(
                reader_code=code,
                full_name=name,
                birth_date=birth_date,
                reader_type=reader_type,
                email=email,
                status="ACTIVE",
            )
            session.add(reader)
            session.flush()
            report.add("reader")
        if _by(session, ReaderCard, card_no=f"THE-{code}") is None:
            session.add(
                ReaderCard(
                    reader_id=reader.id,
                    card_no=f"THE-{code}",
                    issued_at=now - timedelta(days=1),
                    expires_at=add_calendar_months(now, RULES["cardValidityMonths"]),
                    status="ACTIVE",
                    issued_by=actor.id,
                    policy_version_id=policy_id,
                )
            )
            report.add("reader_card")
        first_reader = first_reader or reader.id
    session.flush()

    if link_issuer and link_subject and first_reader is not None:
        account = _by(session, Account, issuer=link_issuer, subject=link_subject)
        if account is not None and account.reader_id != first_reader:
            service.link_reader_account(
                session,
                actor_id=actor.id,
                issuer=link_issuer,
                subject=link_subject,
                reader_id=first_reader,
            )
        report.linked_reader = READERS[0][0]
    return report
