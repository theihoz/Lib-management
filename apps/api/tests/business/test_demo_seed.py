"""seed-demo on the disposable business database (RUN_BUSINESS_DB_TESTS=1)."""

from uuid import uuid4

from sqlalchemy import func, select

from lib_management.catalog.models import BookCopy
from lib_management.circulation.service import active_policy
from lib_management.config import Settings
from lib_management.db import create_engine_from_settings, create_session_factory
from lib_management.demo_seed import READERS, seed_demo
from lib_management.identity import service
from lib_management.identity.models import Account
from lib_management.readers.models import Reader
from tests.business.test_library_flows import pytestmark, settings  # noqa: F401

__all__ = ["pytestmark"]


def test_seed_demo_is_idempotent_and_links_the_reader(settings: Settings):  # noqa: F811
    engine = create_engine_from_settings(settings)
    factory = create_session_factory(engine)
    subject = uuid4().hex
    with factory() as session, session.begin():
        service.seed_rbac(session)
        service.bootstrap_account(
            session,
            issuer="test",
            subject=subject,
            display_name="Độc giả",
            role_codes=["READER"],
        )
    with factory() as session, session.begin():
        first = seed_demo(session, link_issuer="test", link_subject=subject)
    with factory() as session, session.begin():
        second = seed_demo(session, link_issuer="test", link_subject=subject)
        copies = session.scalar(
            select(func.count()).where(BookCopy.barcode.like("DEMO-%"))
        )
        reader = session.scalar(select(Reader).filter_by(reader_code=READERS[0][0]))
        account = session.scalar(select(Account).filter_by(subject=subject))
        assert active_policy(session) is not None
    engine.dispose()

    assert first.created["book_copy"] == copies == 18
    assert second.created == {}
    assert reader is not None and account is not None
    assert account.reader_id == reader.id
