from typing import Annotated

import pytest
from fastapi import Depends, Query
from fastapi.testclient import TestClient

from lib_management.config import Settings
from lib_management.core.errors import Conflict
from lib_management.core.pagination import PageParams, page_params
from lib_management.main import create_app


@pytest.fixture
def client():
    app = create_app(Settings(db_password="unit-test-fixture"))

    @app.get("/test/items")
    def items(
        page: Annotated[PageParams, Depends(page_params)],
        size: Annotated[int, Query(ge=1)] = 1,
    ) -> dict[str, int]:
        return {"limit": page.limit, "size": size}

    @app.get("/test/conflict")
    def conflict() -> None:
        raise Conflict(
            "busy", code="IDEMPOTENCY_IN_PROGRESS", headers={"Retry-After": "1"}
        )

    @app.get("/test/crash")
    def crash() -> None:
        raise RuntimeError("secret detail must not leak")

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


def assert_error(response, status, code):
    assert response.status_code == status
    body = response.json()
    assert set(body) == {"code", "message", "details", "request_id"}
    assert body["code"] == code
    assert body["request_id"] == response.headers["x-request-id"]
    return body


def test_unknown_route_is_error_response(client):
    assert_error(client.get("/api/v1/nope"), 404, "NOT_FOUND")


def test_validation_error_has_details_without_input(client):
    body = assert_error(client.get("/test/items?size=0"), 422, "VALIDATION_ERROR")
    assert body["details"][0]["loc"] == ["query", "size"]
    assert "input" not in body["details"][0]


@pytest.mark.parametrize("query", ["limit=0", "limit=101", "cursor=@@@"])
def test_pagination_bounds(client, query):
    assert_error(client.get(f"/test/items?{query}"), 422, "VALIDATION_ERROR")


def test_pagination_default_limit(client):
    assert client.get("/test/items").json()["limit"] == 20


def test_app_error_keeps_headers(client):
    response = client.get("/test/conflict")
    assert_error(response, 409, "IDEMPOTENCY_IN_PROGRESS")
    assert response.headers["retry-after"] == "1"


def test_unexpected_error_hides_detail(client):
    response = client.get("/test/crash")
    body = assert_error(response, 500, "INTERNAL_ERROR")
    assert "secret detail" not in response.text
    assert body["message"]


def test_valid_request_id_is_echoed(client):
    response = client.get("/api/v1/nope", headers={"X-Request-ID": "abc-12345678"})
    assert response.headers["x-request-id"] == "abc-12345678"
    assert response.json()["request_id"] == "abc-12345678"


@pytest.mark.parametrize(
    "bad", ["short", "has space here", "x" * 101, "semi;colon-123"]
)
def test_invalid_request_id_is_replaced(client, bad):
    response = client.get("/health/live", headers={"X-Request-ID": bad})
    assert response.headers["x-request-id"] != bad
    assert len(response.headers["x-request-id"]) == 36


def test_auth_me_without_oidc_config_is_503(client):
    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer x"})
    assert_error(response, 503, "SERVICE_UNAVAILABLE")
