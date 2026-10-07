import pytest
from pydantic import ValidationError

from lib_management.config import Settings
from lib_management.db import create_engine_from_settings


def test_db_password_is_required():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, db_password="")


def test_db_password_is_missing(monkeypatch):
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_password_special_characters_are_preserved():
    engine = create_engine_from_settings(Settings(db_password="local@:/$_fixture"))
    assert engine.url.password == "local@:/$_fixture"
    engine.dispose()


def test_settings_read_db_environment(monkeypatch):
    monkeypatch.setenv("DB_HOST", "database.test")
    monkeypatch.setenv("DB_PORT", "6543")
    monkeypatch.setenv("DB_USER", "fixture")
    monkeypatch.setenv("DB_NAME", "fixture_db")
    monkeypatch.setenv("DB_PASSWORD", "fixture-password")
    settings = Settings(_env_file=None)
    assert settings.db_host == "database.test"
    assert settings.db_port == 6543
    assert settings.db_user == "fixture"
    assert settings.db_name == "fixture_db"
    assert settings.db_password.get_secret_value() == "fixture-password"


@pytest.mark.parametrize("port", [0, -1, 65536])
def test_db_port_rejects_invalid_tcp_ports(port):
    with pytest.raises(ValidationError):
        Settings(db_password="unit-test-fixture", db_port=port)


@pytest.mark.parametrize("port", [1, 5432, 65535])
def test_db_port_accepts_valid_tcp_ports(port):
    assert Settings(db_password="unit-test-fixture", db_port=port).db_port == port
