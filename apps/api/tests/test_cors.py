from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from lib_management.config import Settings
from lib_management.main import create_app

PAGES = "https://theihoz.github.io"


@pytest.fixture(autouse=True)
def db_probe():
    with patch(
        "lib_management.db.DatabaseProbe.check", new_callable=AsyncMock
    ) as probe:
        probe.return_value = True
        yield probe


def client(origins: str) -> TestClient:
    return TestClient(
        create_app(
            Settings(db_password="unit-test-fixture", cors_allow_origins=origins)
        )
    )


def test_cors_is_off_by_default():
    with client("") as c:
        response = c.get("/health/live", headers={"Origin": PAGES})
    assert "access-control-allow-origin" not in response.headers


def test_allowed_origin_gets_preflight_and_headers():
    with client(f"{PAGES}/, http://localhost:4173") as c:
        preflight = c.options(
            "/api/v1/loans",
            headers={
                "Origin": PAGES,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": (
                    "authorization,content-type,idempotency-key"
                ),
            },
        )
        simple = c.get("/health/live", headers={"Origin": PAGES})
    assert preflight.status_code == 200
    assert preflight.headers["access-control-allow-origin"] == PAGES
    assert simple.headers["access-control-allow-origin"] == PAGES
    assert "X-Request-ID" in simple.headers["access-control-expose-headers"]


def test_other_origins_are_not_allowed():
    with client(PAGES) as c:
        response = c.get("/health/live", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in response.headers


@pytest.mark.parametrize(
    "bad", ["*", "https://theihoz.github.io/Lib-management", "theihoz.github.io"]
)
def test_origin_must_be_scheme_and_host(bad):
    with pytest.raises(ValidationError):
        Settings(db_password="unit-test-fixture", cors_allow_origins=bad)
