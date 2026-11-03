import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from lib_management.identity import service
from lib_management.identity.models import Account, AccountRole
from lib_management.identity.rbac_seed import ROLES
from lib_management.main import create_app
from lib_management.platform.models import AuditLog
from tests.jwt_helpers import ISSUER, make_token, make_verifier


@pytest.fixture
def client(settings, session_factory):
    with session_factory() as session, session.begin():
        service.seed_rbac(session)
    with TestClient(create_app(settings, verifier=make_verifier())) as client:
        yield client


def bootstrap(session_factory, subject="librarian", roles=("LIBRARIAN",)):
    with session_factory() as session, session.begin():
        account = service.bootstrap_account(
            session,
            issuer=ISSUER,
            subject=subject,
            display_name="Thủ thư A",
            role_codes=list(roles),
        )
    return account.id


def me(client, subject="librarian"):
    return client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {make_token(subject)}"}
    )


def test_auth_me_returns_db_permissions(client, session_factory):
    account_id = bootstrap(session_factory)
    response = me(client)
    assert response.status_code == 200
    body = response.json()
    assert body["account"] == {
        "id": str(account_id),
        "reader_id": None,
        "display_name": "Thủ thư A",
        "status": "ACTIVE",
    }
    assert body["permissions"] == sorted(ROLES["LIBRARIAN"][1])


def test_missing_token_is_401(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_TOKEN"


def test_role_claims_in_token_are_ignored(client, session_factory):
    bootstrap(session_factory, roles=("READER",))
    token = make_token("librarian", realm_access={"roles": ["SYSTEM_ADMIN"]})
    body = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    ).json()
    assert "role.manage" not in body["permissions"]


def test_unlinked_subject_is_403_without_jit(client, session_factory):
    response = me(client, "stranger")
    assert response.status_code == 403
    assert response.json()["code"] == "ACCOUNT_NOT_LINKED"
    with session_factory() as session:
        assert session.execute(select(Account)).first() is None


@pytest.mark.parametrize("status", ["LOCKED", "DISABLED"])
def test_inactive_account_with_valid_jwt_is_403(client, session_factory, status):
    account_id = bootstrap(session_factory)
    with session_factory() as session, session.begin():
        session.get(Account, account_id).status = status
    response = me(client)
    assert response.status_code == 403
    assert response.json()["code"] == "ACCOUNT_INACTIVE"


def test_revoked_role_applies_on_next_request(client, session_factory):
    account_id = bootstrap(session_factory)
    assert me(client).json()["permissions"]
    with session_factory() as session, session.begin():
        session.execute(delete(AccountRole).where(AccountRole.account_id == account_id))
    assert me(client).json()["permissions"] == []


def test_require_permission_denies_and_audits(settings, session_factory):
    from typing import Annotated

    from fastapi import Depends

    from lib_management.identity.auth import Principal, require_permission

    with session_factory() as session, session.begin():
        service.seed_rbac(session)
    account_id = bootstrap(session_factory, roles=("READER",))
    app = create_app(settings, verifier=make_verifier())

    @app.post("/test/catalog")
    def write(
        principal: Annotated[Principal, Depends(require_permission("catalog.write"))],
    ) -> dict[str, str]:
        return {"ok": "yes"}

    @app.get("/test/catalog")
    def read(
        principal: Annotated[Principal, Depends(require_permission("catalog.read"))],
    ) -> dict[str, str]:
        return {"ok": "yes"}

    headers = {"Authorization": f"Bearer {make_token('librarian')}"}
    with TestClient(app) as client:
        assert client.get("/test/catalog", headers=headers).status_code == 200
        response = client.post("/test/catalog", headers=headers)
    assert response.status_code == 403
    assert response.json()["code"] == "PERMISSION_DENIED"
    with session_factory() as session:
        entry = session.execute(
            select(AuditLog).where(AuditLog.outcome == "DENIED")
        ).scalar_one()
    assert (entry.actor_id, entry.permission_code) == (account_id, "catalog.write")
    assert entry.request_id == response.headers["x-request-id"]


def test_seed_is_idempotent_and_keeps_extra_grants(session_factory):
    with session_factory() as session, session.begin():
        assert service.seed_rbac(session).changed
    with session_factory() as session, session.begin():
        assert not service.seed_rbac(session).changed


def test_bootstrap_requires_seeded_roles(session_factory):
    with pytest.raises(service.UnknownRole), session_factory() as session:
        service.bootstrap_account(
            session, issuer=ISSUER, subject="x", display_name="x", role_codes=["NOPE"]
        )
