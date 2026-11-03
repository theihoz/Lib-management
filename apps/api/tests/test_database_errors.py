"""Database outages must keep the public error contract and hide credentials."""

import socket

from fastapi.testclient import TestClient

from lib_management.config import Settings
from lib_management.main import create_app
from tests.jwt_helpers import make_token, make_verifier


def test_auth_database_outage_is_503_and_liveness_still_works():
    # Reserve a non-listening port so this exercises a real failed DB connection.
    with socket.socket() as closed_port:
        closed_port.bind(("127.0.0.1", 0))
        settings = Settings(
            db_host="127.0.0.1",
            db_port=closed_port.getsockname()[1],
            db_password="private-database-password",
        )
        app = create_app(settings, verifier=make_verifier())
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {make_token('librarian')}"},
            )
            assert response.status_code == 503
            assert response.json() == {
                "code": "SERVICE_UNAVAILABLE",
                "message": "Dịch vụ tạm thời không sẵn sàng",
                "details": [],
                "request_id": response.headers["x-request-id"],
            }
            assert "private-database-password" not in response.text
            assert "SELECT" not in response.text
            assert client.get("/health/live").status_code == 200
