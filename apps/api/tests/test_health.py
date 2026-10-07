from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from lib_management.config import Settings
from lib_management.main import create_app


@pytest.fixture
def db_probe():
    with patch(
        "lib_management.db.DatabaseProbe.check", new_callable=AsyncMock
    ) as probe:
        yield probe


@pytest.fixture
def client(db_probe):
    with TestClient(create_app(Settings(db_password="unit-test-fixture"))) as client:
        yield client


def test_health_contract(client, db_probe):
    db_probe.return_value = True
    assert client.get("/health/live").json() == {"status": "ok"}
    db_probe.assert_not_called()
    assert client.get("/health/ready").status_code == 200
    assert client.get("/health/ready").json() == {"status": "ready"}
    db_probe.return_value = False
    assert client.get("/health/live").status_code == 200
    response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}


def test_lifespan_disposes_engine():
    engine = MagicMock()
    with patch("lib_management.main.create_engine_from_settings", return_value=engine):
        app = create_app(Settings(db_password="unit-test-fixture"))
        with TestClient(app):
            assert app.state.engine is engine
            engine.dispose.assert_not_called()
        engine.dispose.assert_called_once_with()
