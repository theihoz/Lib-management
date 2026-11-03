from unittest.mock import patch

from lib_management.config import Settings
from lib_management.db import create_engine_from_settings


def test_engine_connection_options():
    with patch("lib_management.db.create_engine") as create:
        create_engine_from_settings(Settings(db_password="unit-test-fixture"))
    assert create.call_args.kwargs == {
        "pool_pre_ping": True,
        "pool_size": 5,
        "max_overflow": 5,
        "pool_timeout": 2.0,
        "pool_recycle": 1800,
        "pool_use_lifo": True,
        "connect_args": {"connect_timeout": 2, "options": "-c statement_timeout=2000"},
    }


def test_pool_bounds_connections_and_releases_capacity(monkeypatch):
    import sqlite3

    import pytest
    from sqlalchemy import create_engine as sqlalchemy_create_engine
    from sqlalchemy.exc import TimeoutError
    from sqlalchemy.pool import QueuePool

    # Real pool behavior, with local SQLite connections replacing PostgreSQL IO.
    def local_engine(url, **options):
        options.pop("connect_args")
        return sqlalchemy_create_engine(
            "sqlite://",
            poolclass=QueuePool,
            creator=lambda: sqlite3.connect(":memory:"),
            **options,
        )

    monkeypatch.setattr("lib_management.db.create_engine", local_engine)
    settings = Settings(
        db_password="unit-test-fixture",
        db_pool_size=1,
        db_pool_max_overflow=0,
        db_pool_timeout_seconds=0.01,
    )
    engine = create_engine_from_settings(settings)
    try:
        with engine.connect() as connection:
            assert connection.exec_driver_sql("SELECT 1").scalar_one() == 1
            with pytest.raises(TimeoutError):
                engine.connect()
        with engine.connect() as recovered:
            assert recovered.exec_driver_sql("SELECT 2").scalar_one() == 2
    finally:
        engine.dispose()
