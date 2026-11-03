"""Disposable PostgreSQL fixture: migrated to head, tables truncated per test.

Requires RUN_DB_INTEGRATION=1 and DB_* pointing at a throwaway database.
"""

import os
from collections.abc import Iterator

import pytest
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session, sessionmaker

from lib_management import migrate
from lib_management.config import Settings
from lib_management.db import create_engine_from_settings, create_session_factory

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_DB_INTEGRATION") != "1",
    reason="Set RUN_DB_INTEGRATION=1 with a disposable PostgreSQL fixture",
)

TABLES = (
    "job",
    "outbox_event",
    "idempotency_record",
    "audit_log",
    "role_permission",
    "account_role",
    "permission",
    "role",
    "account",
)


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    if os.environ.get("RUN_DB_INTEGRATION") == "1":
        return
    skip = pytest.mark.skip(reason="Set RUN_DB_INTEGRATION=1")
    for item in items:
        if "integration" in item.nodeid:
            item.add_marker(skip)


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings()


@pytest.fixture(scope="session")
def engine(settings: Settings) -> Iterator[Engine]:
    migrate.upgrade(settings)
    engine = create_engine_from_settings(settings)
    yield engine
    engine.dispose()


@pytest.fixture
def session_factory(engine: Engine) -> Iterator[sessionmaker[Session]]:
    yield create_session_factory(engine)
    with engine.begin() as connection:
        connection.execute(text(f"TRUNCATE {', '.join(TABLES)} CASCADE"))
