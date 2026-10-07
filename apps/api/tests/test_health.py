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


def test_health_openapi_matches_public_contract(client):
    schema = client.get("/openapi.json").json()
    live = schema["paths"]["/health/live"]["get"]
    ready = schema["paths"]["/health/ready"]["get"]
    assert live["operationId"] == "health_live"
    assert ready["operationId"] == "health_ready"
    cases = (
        (live, "200", "LiveHealth", "ok"),
        (ready, "200", "ReadyHealth", "ready"),
        (ready, "503", "NotReadyHealth", "not_ready"),
    )
    for operation, code, model_name, status in cases:
        assert operation.get("security", []) == []
        payload = operation["responses"][code]["content"]["application/json"]
        assert payload["schema"]["$ref"] == f"#/components/schemas/{model_name}"
        health = schema["components"]["schemas"][model_name]
        assert health["required"] == ["status"]
        assert health["additionalProperties"] is False
        assert health["properties"]["status"]["const"] == status
