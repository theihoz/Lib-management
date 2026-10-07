from unittest.mock import patch

from lib_management.config import Settings
from lib_management.db import create_engine_from_settings


def test_engine_connection_options():
    with patch("lib_management.db.create_engine") as create:
        create_engine_from_settings(Settings(db_password="unit-test-fixture"))
    assert create.call_args.kwargs == {
        "pool_pre_ping": True,
        "connect_args": {"connect_timeout": 2, "options": "-c statement_timeout=2000"},
    }
