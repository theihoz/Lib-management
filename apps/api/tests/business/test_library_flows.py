"""Real PostgreSQL business checks in a database created and dropped by this suite.

RUN_BUSINESS_DB_TESTS=1 enables them. Existing database tables are never truncated.
"""

import os
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg import sql
from sqlalchemy import select

from lib_management import migrate
from lib_management.circulation.models import (
    LoanItem,
    PolicyVersion,
)
from lib_management.circulation.service import RULES, outstanding
from lib_management.config import Settings
from lib_management.db import create_engine_from_settings, create_session_factory
from lib_management.identity.auth import Principal, authenticated
from lib_management.identity.models import Account
from lib_management.identity.rbac_seed import PERMISSIONS
from lib_management.main import create_app

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_BUSINESS_DB_TESTS") != "1",
    reason="Disposable PostgreSQL tests opt in",
)


@pytest.fixture(scope="module")
def settings() -> Iterator[Settings]:
    source = Settings()
    database = "lib_business_test_" + uuid4().hex[:16]
    arguments = dict(
        host=source.db_host,
        port=source.db_port,
        user=source.db_user,
        password=source.db_password.get_secret_value(),
        dbname=source.db_name,
        autocommit=True,
    )
    with psycopg.connect(**arguments) as connection:
        connection.execute(
            sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database))
        )
    isolated = source.model_copy(update={"db_name": database})
    try:
        migrate.upgrade(isolated)
        yield isolated
        # Verify reversibility in the same disposable database.
        migrate.downgrade(isolated, "0002_platform")
        migrate.upgrade(isolated)
    finally:
        with psycopg.connect(**arguments) as connection:
            connection.execute(
                sql.SQL("DROP DATABASE {} WITH (FORCE)").format(
                    sql.Identifier(database)
                )
            )


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    engine = create_engine_from_settings(settings)
    factory = create_session_factory(engine)
    with factory() as session, session.begin():
        account = Account(
            issuer="test",
            subject=uuid4().hex,
            display_name="Test operator",
            status="ACTIVE",
        )
        session.add(account)
        session.flush()
        account_id = account.id
        if session.scalar(select(PolicyVersion.id).limit(1)) is None:
            session.add(
                PolicyVersion(
                    effective_from=datetime.now(UTC) - timedelta(days=1),
                    status="ACTIVE",
                    rules=RULES,
                    rules_schema_version=1,
                    approved_by=account.id,
                    approved_at=datetime.now(UTC) - timedelta(days=2),
                )
            )
    app = create_app(settings)
    with factory() as session:
        account = session.get(Account, account_id)
        assert account is not None
        principal = Principal(account, frozenset(PERMISSIONS))
    app.dependency_overrides[authenticated] = lambda: principal
    with TestClient(app) as http:
        http.test_principal = principal
        yield http
    engine.dispose()


def post(
    client: TestClient, path: str, body: dict | None = None, key: str | None = None
):
    return client.post(
        "/api/v1" + path, json=body, headers={"Idempotency-Key": key or uuid4().hex}
    )


def setup_loan(client: TestClient) -> tuple[dict, dict, dict, dict]:
    code = uuid4().hex[:10]
    location = post(client, "/locations", {"code": code, "name": "Test shelf"})
    assert location.status_code == 201, location.text
    edition = post(
        client,
        "/book-editions",
        {
            "title": "Concurrency in practice " + code,
            "publicationYear": datetime.now(UTC).year,
        },
    )
    assert edition.status_code == 201, edition.text
    copy = post(
        client,
        f"/book-editions/{edition.json()['id']}/copies",
        {"barcodes": [code], "locationId": location.json()["id"]},
    )
    assert copy.status_code == 201, copy.text
    reader = post(
        client,
        "/readers",
        {
            "readerCode": code,
            "fullName": "Test reader",
            "birthDate": "2000-01-01",
            "readerType": "X",
        },
    )
    assert reader.status_code == 201, reader.text
    card = post(client, f"/readers/{reader.json()['id']}/cards")
    assert card.status_code == 201, card.text
    checkout = post(
        client,
        "/loans",
        {"readerId": reader.json()["id"], "copyIds": [copy.json()["id"]]},
    )
    assert checkout.status_code == 201, checkout.text
    return reader.json(), copy.json(), checkout.json(), card.json()


def test_checkout_scanner_renewal_and_good_return(client: TestClient):
    reader, copy, checkout, card = setup_loan(client)
    looked = client.get("/api/v1/copies/lookup", params={"barcode": copy["barcode"]})
    assert looked.status_code == 200, looked.text
    assert looked.json()["loanItem"]["id"] == checkout["items"][0]["loanItemId"]
    matched = client.get("/api/v1/readers/lookup", params={"cardNo": card["card_no"]})
    assert matched.json()["data"][0]["id"] == reader["id"]
    renew = post(
        client, f"/loans/{checkout['loanId']}/renewals", {"expectedVersion": 1}
    )
    assert renew.status_code == 201, renew.text
    rejected = post(
        client, f"/loans/{checkout['loanId']}/renewals", {"expectedVersion": 2}
    )
    assert rejected.status_code == 409
    returned = post(
        client,
        "/returns",
        {"loanItemId": checkout["items"][0]["loanItemId"], "condition": "GOOD"},
    )
    assert returned.status_code == 201, returned.text
    assert returned.json()["copyStatus"] == "AVAILABLE"
    assert (
        post(
            client,
            "/returns",
            {"loanItemId": checkout["items"][0]["loanItemId"], "condition": "GOOD"},
        ).status_code
        == 409
    )


def test_damage_assessment_payment_replay_and_reversal(
    client: TestClient, settings: Settings
):
    reader, copy, checkout, card = setup_loan(client)
    result = post(
        client,
        "/returns",
        {
            "loanItemId": checkout["items"][0]["loanItemId"],
            "condition": "DAMAGE",
            "assessment": {"proposedAmount": "5000", "reason": "Torn pages"},
        },
    )
    assert result.status_code == 201, result.text
    aid = result.json()["assessmentId"]
    eligibility = client.get(f"/api/v1/readers/{reader['id']}/eligibility")
    assert "PENDING_ASSESSMENT" in eligibility.json()["reasons"]
    decided = post(
        client,
        f"/charge-assessments/{aid}/decisions",
        {"expectedVersion": 1, "amount": "5000", "reason": "Repair cost"},
    )
    assert decided.status_code == 201, decided.text
    charges = client.get(
        "/api/v1/fine-charges", params={"readerId": reader["id"]}
    ).json()["data"]
    charge = charges[0]
    payload = {
        "readerId": reader["id"],
        "amount": "5000",
        "method": "CASH",
        "allocations": [{"chargeId": charge["id"], "amount": "5000"}],
    }
    key = uuid4().hex
    payment = post(client, "/payments", payload, key)
    assert payment.status_code == 201, payment.text
    assert post(client, "/payments", payload, key).json() == payment.json()
    payload["amount"] = "1"
    payload["allocations"][0]["amount"] = "1"
    assert post(client, "/payments", payload, key).status_code == 409
    assert post(client, "/payments", payload).status_code == 409
    reversed = post(
        client,
        "/ledger-reversals",
        {
            "entryType": "PAYMENT",
            "entryId": payment.json()["id"],
            "amount": "2000",
            "reason": "Receipt correction",
        },
    )
    assert reversed.status_code == 201, reversed.text
    engine = create_engine_from_settings(settings)
    with create_session_factory(engine)() as session:
        from uuid import UUID

        assert outstanding(session, UUID(reader["id"])) == 2000
    engine.dispose()


def test_public_catalog_does_not_require_auth(client: TestClient):
    client.app.dependency_overrides.pop(authenticated)
    response = client.get("/api/v1/book-editions")
    assert response.status_code == 200, response.text
    assert response.json()["data"]
    assert "publisher_id" not in response.json()["data"][0]


def test_damage_requires_permission_and_no_partial_return(client: TestClient):
    reader, copy, checkout, card = setup_loan(client)
    principal = client.test_principal
    client.app.dependency_overrides[authenticated] = lambda: Principal(
        principal.account, principal.permissions - {"assessment.propose"}
    )
    denied = post(
        client,
        "/returns",
        {
            "loanItemId": checkout["items"][0]["loanItemId"],
            "condition": "LOST",
            "assessment": {"proposedAmount": "500", "reason": "Lost book"},
        },
    )
    assert denied.status_code == 403
    still_open = client.get(
        "/api/v1/copies/lookup", params={"barcode": copy["barcode"]}
    ).json()
    assert still_open["loanItem"]["closed_at"] is None


def test_stale_reader_patch_and_invalid_policy(client: TestClient):
    reader, copy, checkout, card = setup_loan(client)
    response = client.patch(
        "/api/v1/readers/" + reader["id"],
        json={"expectedVersion": 8, "fullName": "New name"},
    )
    assert response.status_code == 409
    policy = post(
        client,
        "/policy-versions",
        {
            "effectiveFrom": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
            "rulesSchemaVersion": 1,
            "rules": {**RULES, "maxBooksPerLoan": 20},
        },
    )
    assert policy.status_code == 422


def test_hold_ready_cancel_and_pickup(client: TestClient):
    reader, copy, checkout, card = setup_loan(client)
    post(
        client,
        "/returns",
        {"loanItemId": checkout["items"][0]["loanItemId"], "condition": "GOOD"},
    )
    held = post(
        client,
        "/reservations",
        {"readerId": reader["id"], "editionId": copy["edition_id"]},
    )
    assert held.status_code == 201, held.text
    assert held.json()["status"] == "READY"
    picked = post(
        client,
        f"/reservations/{held.json()['id']}/pickups",
        {"expectedVersion": held.json()["version"]},
    )
    assert picked.status_code == 201, picked.text
    assert picked.json()["items"][0]["copyId"] == copy["id"]


def test_overdue_items_include_reader_title_and_late_days(
    client: TestClient, settings: Settings
):
    reader, copy, checkout, _ = setup_loan(client)
    item_id = checkout["items"][0]["loanItemId"]
    engine = create_engine_from_settings(settings)
    with create_session_factory(engine)() as session, session.begin():
        item = session.get(LoanItem, item_id)
        assert item is not None
        item.issued_at = datetime.now(UTC) - timedelta(days=10)
        item.due_at = datetime.now(UTC) - timedelta(days=3)
    engine.dispose()
    cursor = None
    found = None
    while found is None:
        page = client.get(
            "/api/v1/overdue-items",
            params={"limit": 100, **({"cursor": cursor} if cursor else {})},
        )
        assert page.status_code == 200, page.text
        found = next(
            (row for row in page.json()["data"] if row["loanItem"]["id"] == item_id),
            None,
        )
        cursor = page.json()["nextCursor"]
        if not cursor:
            break
    assert found is not None
    assert found["reader"]["full_name"] == "Test reader"
    assert found["reader"]["id"] == reader["id"]
    assert found["title"].startswith("Concurrency in practice")
    assert found["lateDays"] >= 3
    # Returning the item removes it from the overdue list.
    assert (
        post(
            client, "/returns", {"loanItemId": item_id, "condition": "GOOD"}
        ).status_code
        == 201
    )
