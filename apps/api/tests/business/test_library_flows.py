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
    FineCharge,
    LoanItem,
    PolicyVersion,
)
from lib_management.circulation.service import (
    RULES,
    RULES_SCHEMA_VERSION,
    outstanding,
)
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
                    rules_schema_version=RULES_SCHEMA_VERSION,
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
            "rules": RULES,
        },
    )
    assert policy.status_code == 422


def test_hold_ready_cancel_and_pickup(client: TestClient):
    # Lab 2 YC9: reserve only a book that is out; the return makes it READY (FIFO).
    reader, copy, checkout, card = setup_loan(client)
    other = new_reader(client)
    assert post(client, f"/readers/{other.json()['id']}/cards").status_code == 201
    held = post(
        client,
        "/reservations",
        {"readerId": other.json()["id"], "editionId": copy["edition_id"]},
    )
    assert held.status_code == 201, held.text
    assert held.json()["status"] == "QUEUED"
    post(
        client,
        "/returns",
        {"loanItemId": checkout["items"][0]["loanItemId"], "condition": "GOOD"},
    )
    ready = client.get(
        "/api/v1/reservations",
        params={"readerId": other.json()["id"], "status": "READY"},
    ).json()["data"]
    assert [row["id"] for row in ready] == [held.json()["id"]]
    picked = post(
        client,
        f"/reservations/{held.json()['id']}/pickups",
        {"expectedVersion": ready[0]["version"]},
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


def add_charge(
    client: TestClient, settings: Settings, reader: dict, checkout: dict, amount: int
) -> None:
    from uuid import UUID

    engine = create_engine_from_settings(settings)
    with create_session_factory(engine)() as session, session.begin():
        item = session.get(LoanItem, UUID(checkout["items"][0]["loanItemId"]))
        assert item is not None
        session.add(
            FineCharge(
                reader_id=UUID(reader["id"]),
                loan_item_id=item.id,
                policy_version_id=item.policy_version_id,
                reason="MANUAL",
                assessed_amount=amount,
                calculation={"test": True},
                manual_reason="test",
                assessed_by=client.test_principal.account_id,
            )
        )
    engine.dispose()


def reasons(client: TestClient, reader: dict) -> list[str]:
    response = client.get(f"/api/v1/readers/{reader['id']}/eligibility")
    assert response.status_code == 200, response.text
    return response.json()["reasons"]


def test_outstanding_balance_blocks_only_above_threshold(
    client: TestClient, settings: Settings
):
    # QĐ12: default threshold 50.000 VND; borrowing is blocked only above it.
    reader, _, checkout, _ = setup_loan(client)
    add_charge(client, settings, reader, checkout, 49_999)
    assert "OUTSTANDING_BALANCE" not in reasons(client, reader)
    add_charge(client, settings, reader, checkout, 1)
    assert "OUTSTANDING_BALANCE" not in reasons(client, reader)
    add_charge(client, settings, reader, checkout, 1)
    assert "OUTSTANDING_BALANCE" in reasons(client, reader)


def policy_body(**rules: object) -> dict:
    return {
        "effectiveFrom": (datetime.now(UTC) + timedelta(days=30)).isoformat(),
        "rulesSchemaVersion": RULES_SCHEMA_VERSION,
        "rules": {**RULES, **rules},
    }


@pytest.mark.parametrize(
    "rules",
    [
        {"allowedOutstandingBalance": "0"},
        {"overdueFinePerDay": "-1"},
        {"initialLoanDays": 0},
        {"readyHoldDays": 0},
        {"minReaderAge": 60, "maxReaderAge": 55},
        {"damageLostFees": {**RULES["damageLostFees"], "LOST": "700000"}},
        {"libraryName": ""},
        {"unknownRule": 1},
    ],
)
def test_policy_rejects_invalid_values(client: TestClient, rules: dict):
    # QĐ17: fine >= 0, threshold > 0, day counts positive; QĐ07 lost-fee range.
    assert post(client, "/policy-versions", policy_body(**rules)).status_code == 422


def test_policy_accepts_manager_values(client: TestClient):
    # QĐ16/QĐ17: the Manager may change configured values in a new draft.
    body = policy_body(
        libraryName="Thư viện Nhóm 3",
        overdueFinePerDay="2000",
        allowedOutstandingBalance="80000",
        readyHoldDays=2,
        initialLoanDays=5,
    )
    created = post(client, "/policy-versions", body)
    assert created.status_code == 201, created.text
    assert created.json()["status"] == "DRAFT"
    assert created.json()["rules_schema_version"] == RULES_SCHEMA_VERSION
    assert created.json()["rules"]["allowedOutstandingBalance"] == "80000"
    assert created.json()["rules"]["libraryName"] == "Thư viện Nhóm 3"


def test_checkout_respects_policy_book_limit(client: TestClient):
    # QĐ05: at most maxBooksPerLoan (4) copies in one loan.
    reader, first, _, _ = setup_loan(client)
    code = uuid4().hex[:8]
    edition = post(
        client,
        "/book-editions",
        {"title": "Limit " + code, "publicationYear": datetime.now(UTC).year},
    )
    copies = post(
        client,
        f"/book-editions/{edition.json()['id']}/copies",
        {
            "barcodes": [f"{code}-{n}" for n in range(5)],
            "locationId": first["location_id"],
        },
    )
    assert copies.status_code == 201, copies.text
    listed = client.get(
        f"/api/v1/book-editions/{edition.json()['id']}/copies", params={"limit": 10}
    )
    ids = [row["id"] for row in listed.json()["data"]]
    assert len(ids) == 5
    too_many = post(client, "/loans", {"readerId": reader["id"], "copyIds": ids})
    assert too_many.status_code == 422, too_many.text
    assert "QĐ05" in too_many.json()["message"]
    allowed = post(client, "/loans", {"readerId": reader["id"], "copyIds": ids[:4]})
    assert allowed.status_code == 201, allowed.text


def test_lost_fee_must_follow_qd07_range(client: TestClient):
    reader, copy, checkout, _ = setup_loan(client)
    item = checkout["items"][0]["loanItemId"]

    def lost(amount: str):
        return post(
            client,
            "/returns",
            {
                "loanItemId": item,
                "condition": "LOST",
                "assessment": {"proposedAmount": amount, "reason": "Mất sách"},
            },
        )

    assert lost("50000").status_code == 422
    assert lost("700000").status_code == 422
    accepted = lost("100000")
    assert accepted.status_code == 201, accepted.text
    aid = accepted.json()["assessmentId"]
    too_high = post(
        client,
        f"/charge-assessments/{aid}/decisions",
        {"expectedVersion": 1, "amount": "650000", "reason": "Giá sách"},
    )
    assert too_high.status_code == 422
    approved = post(
        client,
        f"/charge-assessments/{aid}/decisions",
        {"expectedVersion": 1, "amount": "600000", "reason": "Giá sách"},
    )
    assert approved.status_code == 201, approved.text


def birth_for_age(age: int) -> str:
    from zoneinfo import ZoneInfo

    today = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).date()
    try:
        born = today.replace(year=today.year - age)
    except ValueError:  # 29 February in a non-leap year
        born = today.replace(year=today.year - age, day=28)
    return born.isoformat()


def new_reader(client: TestClient, **fields: object):
    return post(
        client,
        "/readers",
        {
            "readerCode": uuid4().hex[:12],
            "fullName": "Độc giả kiểm thử",
            "birthDate": birth_for_age(30),
            "readerType": "Y",
            **fields,
        },
    )


def test_reader_type_must_be_x_y_or_z(client: TestClient):
    # BM02: loại độc giả X, Y, Z.
    assert new_reader(client, readerType="A").status_code == 422
    assert new_reader(client, readerType="Z").status_code == 201


@pytest.mark.parametrize(
    ("age", "status"), [(11, 422), (12, 201), (55, 201), (56, 422)]
)
def test_reader_age_follows_qd01(client: TestClient, age: int, status: int):
    response = new_reader(client, birthDate=birth_for_age(age))
    assert response.status_code == status, response.text


def test_reader_email_is_unique_ignoring_case(client: TestClient):
    email = f"dg.{uuid4().hex[:8]}@example.test"
    first = new_reader(client, email=email)
    assert first.status_code == 201, first.text
    duplicate = new_reader(client, email=email.upper())
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "EMAIL_TAKEN"
    other = new_reader(client)
    taken = client.patch(
        "/api/v1/readers/" + other.json()["id"],
        json={"expectedVersion": 1, "email": email},
    )
    assert taken.status_code == 409
    same = client.patch(
        "/api/v1/readers/" + first.json()["id"],
        json={"expectedVersion": 1, "email": email},
    )
    assert same.status_code == 200, same.text


def main_category(client: TestClient, code: str) -> dict:
    page = client.get("/api/v1/categories", params={"query": f"Thể loại {code}"})
    assert page.status_code == 200, page.text
    return next(row for row in page.json()["data"] if row["code"] == code)


def test_categories_hang_below_main_a_b_c(client: TestClient):
    # QĐ04: three main categories A, B, C; no other root may be created.
    roots = {code: main_category(client, code) for code in ("A", "B", "C")}
    assert all(row["is_root"] for row in roots.values())
    code = uuid4().hex[:6]
    orphan = post(client, "/categories", {"code": "R" + code, "name": "Gốc " + code})
    assert orphan.status_code == 422
    child = post(
        client,
        "/categories",
        {
            "code": "A1" + code,
            "name": "Nhánh A.1 " + code,
            "parentId": roots["A"]["id"],
        },
    )
    assert child.status_code == 201, child.text
    grandchild = post(
        client,
        "/categories",
        {
            "code": "A11" + code,
            "name": "Nhánh A.1.1 " + code,
            "parentId": child.json()["id"],
        },
    )
    assert grandchild.status_code == 201, grandchild.text
    detached = client.patch(
        "/api/v1/categories/" + child.json()["id"], json={"parentId": None}
    )
    assert detached.status_code == 422
    protected = client.patch(
        "/api/v1/categories/" + roots["B"]["id"], json={"name": "Đổi tên"}
    )
    assert protected.status_code == 409


def test_category_name_is_unique(client: TestClient):
    # QĐ09: mã và tên thể loại là duy nhất.
    parent = main_category(client, "C")["id"]
    name = "Kinh tế học " + uuid4().hex[:6]
    first = post(
        client,
        "/categories",
        {"code": uuid4().hex[:8], "name": name, "parentId": parent},
    )
    assert first.status_code == 201, first.text
    same = post(
        client,
        "/categories",
        {"code": uuid4().hex[:8], "name": name.upper(), "parentId": parent},
    )
    assert same.status_code == 409
    assert same.json()["code"] == "CATEGORY_NAME_TAKEN"


def report_period(days: int = 1) -> dict[str, str]:
    from zoneinfo import ZoneInfo

    zone = ZoneInfo("Asia/Ho_Chi_Minh")
    tomorrow = datetime.now(zone).replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow += timedelta(days=1)
    return {
        "from": (tomorrow - timedelta(days=days)).isoformat(),
        "to": tomorrow.isoformat(),
    }


def request_report(client: TestClient, report_type: str, export: bool = False, **f):
    response = post(
        client,
        "/export-jobs" if export else "/report-jobs",
        {"reportType": report_type, "filters": {**report_period(), **f}},
    )
    assert response.status_code == 202, response.text
    return response.json()["jobId"]


def run_report(settings: Settings, job_id: str, tmp_path, export: bool = False):
    from uuid import UUID

    from lib_management.platform.models import Job
    from lib_management.reporting.handlers import report_handler
    from lib_management.reporting.models import ReportJob
    from lib_management.reporting.service import snapshot
    from lib_management.reporting.storage import FileArtifactStorage
    from lib_management.worker.registry import JobContext

    engine = create_engine_from_settings(settings)
    factory = create_session_factory(engine)
    with factory() as session:
        report = session.scalar(
            select(ReportJob).where(ReportJob.job_id == UUID(job_id))
        )
        assert report is not None
        result = snapshot(session, report, datetime.now(UTC))
    handler = report_handler(factory, FileArtifactStorage(tmp_path), timedelta(hours=1))
    handler(
        JobContext(
            job_id=job_id,
            job_type="export" if export else "report",
            attempt=1,
            payload={"report_id": str(report.id)},
            heartbeat=lambda: True,
        )
    )
    with factory() as session, session.begin():
        job = session.get(Job, UUID(job_id))
        assert job is not None
        job.status = "SUCCEEDED"  # what the runner does after the handler returns
    engine.dispose()
    return result


def test_bm08_reports_rank_and_count_loans(client, settings, tmp_path):
    reader, copy, checkout, _ = setup_loan(client)
    add_charge(client, settings, reader, checkout, 3000)
    overview = run_report(settings, request_report(client, "OVERVIEW"), tmp_path)
    metrics = overview["metrics"]
    assert metrics["loan_items_issued"] >= 1
    assert metrics["copies_on_loan"] >= 1
    assert int(metrics["fines_assessed"]) >= 3000
    assert overview["rows"] == []
    trend = run_report(
        settings, request_report(client, "LOAN_TREND", granularity="day"), tmp_path
    )["rows"]
    assert trend and trend[-1]["loans_issued"] >= 1
    top = run_report(settings, request_report(client, "TOP_BOOKS", limit=100), tmp_path)
    counts = [row["loan_count"] for row in top["rows"]]
    assert counts == sorted(counts, reverse=True)
    assert copy["edition_id"] in {row["edition_id"] for row in top["rows"]}
    readers = run_report(
        settings, request_report(client, "ACTIVE_READERS", limit=100), tmp_path
    )["rows"]
    mine = next(row for row in readers if row["reader_id"] == reader["id"])
    assert mine["loan_count"] == 1 and mine["fines_amount"] == "3000"
    inventory = run_report(settings, request_report(client, "INVENTORY"), tmp_path)
    line = next(r for r in inventory["rows"] if r["edition_id"] == copy["edition_id"])
    assert line["total_copies"] == 1 and line["on_loan"] == 1
    loans = run_report(
        settings, request_report(client, "LOAN_CSV", export=True), tmp_path, export=True
    )
    assert any(row["reader_code"] == reader["reader_code"] for row in loans["rows"])
    fines = run_report(
        settings, request_report(client, "FINE_CSV", export=True), tmp_path, export=True
    )
    fine = next(
        row for row in fines["rows"] if row["reader_code"] == reader["reader_code"]
    )
    assert fine["balance"] == "3000"


def test_report_period_follows_qd13(client: TestClient):
    period = report_period()
    later = datetime.fromisoformat(period["to"]) + timedelta(days=1)
    future = post(
        client,
        "/report-jobs",
        {"reportType": "OVERVIEW", "filters": {**period, "to": later.isoformat()}},
    )
    assert future.status_code == 422
    reversed_period = post(
        client,
        "/report-jobs",
        {
            "reportType": "OVERVIEW",
            "filters": {"from": period["to"], "to": period["from"]},
        },
    )
    assert reversed_period.status_code == 422


def test_export_without_data_creates_no_file(client, settings, tmp_path):
    # QĐ26: nothing matches, so no file is created and the download says so.
    response = post(
        client,
        "/export-jobs",
        {
            "reportType": "FINE_CSV",
            "filters": {
                "from": "2001-01-01T00:00:00+07:00",
                "to": "2001-01-02T00:00:00+07:00",
            },
        },
    )
    assert response.status_code == 202, response.text
    job_id = response.json()["jobId"]
    run_report(settings, job_id, tmp_path, export=True)
    assert list(tmp_path.iterdir()) == []
    link = client.get(f"/api/v1/export-jobs/{job_id}/download")
    assert link.status_code == 409, link.text
    assert link.json()["code"] == "NO_DATA"


def patch_copy(client: TestClient, copy_id: str, key: str | None = None, **body):
    return client.patch(
        f"/api/v1/copies/{copy_id}",
        json=body,
        headers={"Idempotency-Key": key or uuid4().hex},
    )


def test_copy_status_transitions_follow_yc2(client: TestClient):
    reader, copy, checkout, _ = setup_loan(client)
    # On loan: locked until returned (D1).
    locked = patch_copy(
        client, copy["id"], expectedVersion=2, status="REPAIR", reason="x"
    )
    assert locked.status_code == 409 and locked.json()["code"] == "COPY_STATUS_LOCKED"
    post(
        client,
        "/returns",
        {"loanItemId": checkout["items"][0]["loanItemId"], "condition": "GOOD"},
    )
    current = client.get(f"/api/v1/book-editions/{copy['edition_id']}/copies").json()[
        "data"
    ][0]
    assert current["status"] == "AVAILABLE"
    no_reason = patch_copy(
        client, copy["id"], expectedVersion=current["version"], status="MAINTENANCE"
    )
    assert no_reason.status_code == 422
    key = uuid4().hex
    body = {
        "expectedVersion": current["version"],
        "status": "MAINTENANCE",
        "reason": "Bọc lại bìa",
    }
    moved = patch_copy(client, copy["id"], key, **body)
    assert moved.status_code == 200, moved.text
    assert moved.json()["status"] == "MAINTENANCE"
    assert patch_copy(client, copy["id"], key, **body).json() == moved.json()
    stale = patch_copy(client, copy["id"], **body)
    assert stale.status_code == 409
    lost = patch_copy(
        client,
        copy["id"],
        expectedVersion=moved.json()["version"],
        status="LOST",
        reason="Không tìm thấy khi kiểm kê",
    )
    assert lost.status_code == 200, lost.text
    found = patch_copy(
        client, copy["id"], expectedVersion=lost.json()["version"], status="AVAILABLE"
    )
    assert found.status_code == 200 and found.json()["status"] == "AVAILABLE"


def test_repaired_copy_goes_to_waiting_reservation(
    client: TestClient, settings: Settings
):
    from lib_management.circulation.models import Reservation

    reader, copy, checkout, _ = setup_loan(client)
    other = new_reader(client)
    assert post(client, f"/readers/{other.json()['id']}/cards").status_code == 201
    held = post(
        client,
        "/reservations",
        {"readerId": other.json()["id"], "editionId": copy["edition_id"]},
    )
    assert held.status_code == 201, held.text
    assert held.json()["status"] == "QUEUED"
    returned = post(
        client,
        "/returns",
        {
            "loanItemId": checkout["items"][0]["loanItemId"],
            "condition": "DAMAGE",
            "assessment": {"proposedAmount": "20000", "reason": "Rách bìa"},
        },
    )
    assert returned.status_code == 201, returned.text
    current = client.get(f"/api/v1/book-editions/{copy['edition_id']}/copies").json()[
        "data"
    ][0]
    assert current["status"] == "REPAIR"
    repaired = patch_copy(
        client, copy["id"], expectedVersion=current["version"], status="AVAILABLE"
    )
    assert repaired.status_code == 200, repaired.text
    engine = create_engine_from_settings(settings)
    with create_session_factory(engine)() as session:
        reservation = session.get(Reservation, held.json()["id"])
        assert reservation is not None and reservation.status == "READY"
    engine.dispose()


def card_status(client: TestClient, card: dict, version: int, status: str, reason=None):
    return client.patch(
        f"/api/v1/reader-cards/{card['id']}",
        json={"expectedVersion": version, "status": status, "reason": reason},
        headers={"Idempotency-Key": uuid4().hex},
    )


def test_card_block_and_unblock_follow_yc6(client: TestClient):
    reader, copy, checkout, card = setup_loan(client)
    no_reason = card_status(client, card, card["version"], "BLOCKED")
    assert no_reason.status_code == 422
    blocked = card_status(
        client, card, card["version"], "BLOCKED", "Mất thẻ, chờ cấp lại"
    )
    assert blocked.status_code == 200, blocked.text
    assert blocked.json()["status"] == "BLOCKED"
    assert "CARD_BLOCKED" in reasons(client, reader)
    post(
        client,
        "/returns",
        {"loanItemId": checkout["items"][0]["loanItemId"], "condition": "GOOD"},
    )
    refused = post(
        client, "/loans", {"readerId": reader["id"], "copyIds": [copy["id"]]}
    )
    assert refused.status_code == 422
    assert "CARD_BLOCKED" in refused.json()["details"][0]["reasons"]
    same = card_status(client, card, blocked.json()["version"], "BLOCKED", "again")
    assert same.status_code == 409
    unblocked = card_status(client, card, blocked.json()["version"], "ACTIVE")
    assert unblocked.status_code == 200, unblocked.text
    assert "CARD_BLOCKED" not in reasons(client, reader)
    listed = client.get(f"/api/v1/readers/{reader['id']}/cards")
    assert listed.status_code == 200
    assert [row["status"] for row in listed.json()] == ["ACTIVE"]


def test_revoked_or_expired_card_cannot_be_unblocked(client, settings):
    from uuid import UUID

    from lib_management.readers.models import ReaderCard

    reader, _, _, card = setup_loan(client)
    reissued = post(client, f"/readers/{reader['id']}/cards")
    assert reissued.status_code == 201
    revoked = client.get(f"/api/v1/readers/{reader['id']}/cards").json()[-1]
    assert revoked["id"] == card["id"] and revoked["status"] == "REVOKED"
    assert card_status(client, revoked, revoked["version"], "ACTIVE").status_code == 409
    current = reissued.json()
    blocked = card_status(client, current, current["version"], "BLOCKED", "Tạm khóa")
    engine = create_engine_from_settings(settings)
    with create_session_factory(engine)() as session, session.begin():
        row = session.get(ReaderCard, UUID(current["id"]))
        assert row is not None
        row.issued_at = datetime.now(UTC) - timedelta(days=200)
        row.expires_at = datetime.now(UTC) - timedelta(days=1)
    engine.dispose()
    expired = card_status(client, current, blocked.json()["version"], "ACTIVE")
    assert expired.status_code == 409 and expired.json()["code"] == "CARD_EXPIRED"


def test_manual_fine_is_proposed_then_decided(client: TestClient):
    # YC#11 / D2: the Librarian proposes, the Manager decides (like C03).
    reader, copy, checkout, _ = setup_loan(client)
    other, _, other_checkout, _ = setup_loan(client)
    foreign = post(
        client,
        "/charge-assessments",
        {
            "readerId": reader["id"],
            "loanItemId": other_checkout["items"][0]["loanItemId"],
            "proposedAmount": "10000",
            "reason": "Làm bẩn sách",
        },
    )
    assert foreign.status_code == 422
    assert (
        post(
            client,
            "/charge-assessments",
            {"readerId": reader["id"], "proposedAmount": "0", "reason": "x"},
        ).status_code
        == 422
    )
    proposed = post(
        client,
        "/charge-assessments",
        {
            "readerId": reader["id"],
            "loanItemId": checkout["items"][0]["loanItemId"],
            "proposedAmount": "15000",
            "reason": "Viết vào sách",
        },
    )
    assert proposed.status_code == 201, proposed.text
    assert (
        proposed.json()["kind"] == "MANUAL" and proposed.json()["status"] == "PENDING"
    )
    assert "PENDING_ASSESSMENT" in reasons(client, reader)
    decided = post(
        client,
        f"/charge-assessments/{proposed.json()['id']}/decisions",
        {"expectedVersion": 1, "amount": "15000", "reason": "Đúng quy định"},
    )
    assert decided.status_code == 201, decided.text
    charges = client.get("/api/v1/fine-charges", params={"readerId": reader["id"]})
    manual = [row for row in charges.json()["data"] if row["reason"] == "MANUAL"]
    assert len(manual) == 1 and manual[0]["assessed_amount"] == "15000"
    assert "PENDING_ASSESSMENT" not in reasons(client, reader)
    unlinked = post(
        client,
        "/charge-assessments",
        {"readerId": reader["id"], "proposedAmount": "5000", "reason": "Ồn ào"},
    )
    assert unlinked.status_code == 201, unlinked.text
    closed = post(
        client,
        f"/charge-assessments/{unlinked.json()['id']}/decisions",
        {"expectedVersion": 1, "amount": "0", "reason": "Nhắc nhở, không phạt"},
    )
    assert closed.status_code == 201 and closed.json()["status"] == "CLOSED_NO_CHARGE"


def test_manual_fine_needs_propose_permission(client: TestClient):
    reader, _, _, _ = setup_loan(client)
    principal = client.test_principal
    client.app.dependency_overrides[authenticated] = lambda: Principal(
        principal.account, principal.permissions - {"assessment.propose"}
    )
    denied = post(
        client,
        "/charge-assessments",
        {"readerId": reader["id"], "proposedAmount": "1000", "reason": "x"},
    )
    assert denied.status_code == 403


def test_reader_profile_data_for_yc17(client: TestClient, settings: Settings):
    reader, copy, checkout, _ = setup_loan(client)
    add_charge(client, settings, reader, checkout, 8000)
    charges = client.get("/api/v1/fine-charges", params={"readerId": reader["id"]})
    charge = charges.json()["data"][0]
    assert charge["balance"] == "8000"
    paid = post(
        client,
        "/payments",
        {
            "readerId": reader["id"],
            "amount": "3000",
            "method": "CASH",
            "allocations": [{"chargeId": charge["id"], "amount": "3000"}],
        },
    )
    assert paid.status_code == 201, paid.text
    after = client.get("/api/v1/fine-charges", params={"readerId": reader["id"]})
    assert after.json()["data"][0]["balance"] == "5000"
    loans = client.get(
        "/api/v1/loans", params={"readerId": reader["id"], "status": "OPEN"}
    ).json()["data"]
    assert len(loans) == 1 and loans[0]["title"].startswith("Concurrency in practice")
    other = new_reader(client)
    post(client, f"/readers/{other.json()['id']}/cards")
    held = post(
        client,
        "/reservations",
        {"readerId": other.json()["id"], "editionId": copy["edition_id"]},
    )
    assert held.status_code == 201, held.text
    active = client.get(
        "/api/v1/reservations",
        params={"readerId": other.json()["id"], "status": "ACTIVE"},
    )
    assert [row["id"] for row in active.json()["data"]] == [held.json()["id"]]
    none = client.get(
        "/api/v1/reservations",
        params={"readerId": other.json()["id"], "status": "EXPIRED"},
    )
    assert none.json()["data"] == []


def test_book_search_by_author_and_category_tree(client: TestClient):
    tag = uuid4().hex[:6]
    author = post(client, "/authors", {"name": f"Tác giả {tag}"})
    assert author.status_code == 201, author.text
    root = main_category(client, "B")
    branch = post(
        client,
        "/categories",
        {"code": "B-" + tag, "name": "Nhánh B " + tag, "parentId": root["id"]},
    )
    leaf = post(
        client,
        "/categories",
        {"code": "BB-" + tag, "name": "Lá B " + tag, "parentId": branch.json()["id"]},
    )
    edition = post(
        client,
        "/book-editions",
        {
            "title": "Sách tìm kiếm " + tag,
            "publicationYear": datetime.now(UTC).year,
            "authorIds": [author.json()["id"]],
            "categoryIds": [leaf.json()["id"]],
        },
    )
    assert edition.status_code == 201, edition.text

    def ids(**params: str) -> set[str]:
        page = client.get("/api/v1/book-editions", params={"limit": 100, **params})
        assert page.status_code == 200, page.text
        return {row["id"] for row in page.json()["data"]}

    assert edition.json()["id"] in ids(query=f"tác giả {tag}")
    assert edition.json()["id"] in ids(categoryId=branch.json()["id"])
    assert edition.json()["id"] in ids(categoryId=root["id"], query=tag)
    other = main_category(client, "C")
    assert edition.json()["id"] not in ids(categoryId=other["id"])


def test_edition_deactivation_follows_d4(client: TestClient):
    reader, copy, checkout, _ = setup_loan(client)
    edition_id = copy["edition_id"]
    busy = client.patch(
        f"/api/v1/book-editions/{edition_id}",
        json={"expectedVersion": 1, "status": "INACTIVE"},
    )
    assert busy.status_code == 409 and busy.json()["code"] == "EDITION_IN_USE"
    post(
        client,
        "/returns",
        {"loanItemId": checkout["items"][0]["loanItemId"], "condition": "GOOD"},
    )
    done = client.patch(
        f"/api/v1/book-editions/{edition_id}",
        json={"expectedVersion": 1, "status": "INACTIVE"},
    )
    assert done.status_code == 200, done.text
    assert client.get(f"/api/v1/book-editions/{edition_id}").status_code == 404


def as_reader(client: TestClient, settings: Settings, reader: dict) -> None:
    from uuid import UUID

    from lib_management.identity.rbac_seed import ROLES

    engine = create_engine_from_settings(settings)
    with create_session_factory(engine)() as session, session.begin():
        account = Account(
            issuer="test",
            subject=uuid4().hex,
            display_name="Reader",
            status="ACTIVE",
            reader_id=UUID(reader["id"]),
        )
        session.add(account)
    with create_session_factory(engine)() as session:
        account = session.scalar(select(Account).where(Account.id == account.id))
    engine.dispose()
    principal = Principal(account, frozenset(ROLES["READER"][1]))
    client.app.dependency_overrides[authenticated] = lambda: principal


def test_reader_renews_only_own_loan(client: TestClient, settings: Settings):
    # YC#9 (Ai: Độc giả) with C06 scope.
    reader, _, checkout, _ = setup_loan(client)
    _, _, other_checkout, _ = setup_loan(client)
    as_reader(client, settings, reader)
    mine = client.get("/api/v1/me/loans").json()["data"]
    assert [row["loan"]["id"] for row in mine] == [checkout["loanId"]]
    assert mine[0]["title"].startswith("Concurrency in practice")
    other = post(
        client, f"/loans/{other_checkout['loanId']}/renewals", {"expectedVersion": 1}
    )
    assert other.status_code == 404
    renewed = post(
        client,
        f"/loans/{checkout['loanId']}/renewals",
        {"expectedVersion": mine[0]["loan"]["version"]},
    )
    assert renewed.status_code == 201, renewed.text
    history = client.get("/api/v1/me/loans", params={"status": "ALL"}).json()["data"]
    assert len(history) == 1


def test_dashboard_lists_overdue_and_top_books(client: TestClient, settings: Settings):
    # YC#19 / BM14.
    reader, copy, checkout, _ = setup_loan(client)
    item_id = checkout["items"][0]["loanItemId"]
    engine = create_engine_from_settings(settings)
    with create_session_factory(engine)() as session, session.begin():
        item = session.get(LoanItem, item_id)
        assert item is not None
        item.issued_at = datetime.now(UTC) - timedelta(days=6)
        item.due_at = datetime.now(UTC) - timedelta(days=2)
    engine.dispose()
    setup_loan(client)  # one loan issued today
    board = client.get("/api/v1/dashboard")
    assert board.status_code == 200, board.text
    data = board.json()
    assert data["overdueCount"] >= 1 and data["loansToday"] >= 1
    assert len(data["overdueTop"]) <= 10 and len(data["topBooks30d"]) <= 5
    counts = [row["loan_count"] for row in data["topBooks30d"]]
    assert counts == sorted(counts, reverse=True)
    principal = client.test_principal
    client.app.dependency_overrides[authenticated] = lambda: Principal(
        principal.account, principal.permissions - {"overdue.read"}
    )
    assert client.get("/api/v1/dashboard").status_code == 403


def test_reservation_needs_all_copies_out_and_respects_limit(client: TestClient):
    reader, copy, checkout, _ = setup_loan(client)
    post(
        client,
        "/returns",
        {"loanItemId": checkout["items"][0]["loanItemId"], "condition": "GOOD"},
    )
    available = post(
        client,
        "/reservations",
        {"readerId": reader["id"], "editionId": copy["edition_id"]},
    )
    assert available.status_code == 409
    assert available.json()["code"] == "COPY_AVAILABLE"
    # D3: on loan + reserved < maxActiveLoansAndHolds (4).
    holder = new_reader(client)
    assert post(client, f"/readers/{holder.json()['id']}/cards").status_code == 201
    editions = []
    for _ in range(5):
        _, out, _, _ = setup_loan(client)  # someone else holds the only copy
        editions.append(out["edition_id"])
    codes = [
        post(
            client,
            "/reservations",
            {"readerId": holder.json()["id"], "editionId": edition},
        )
        for edition in editions
    ]
    assert [r.status_code for r in codes[:4]] == [201] * 4
    assert codes[4].status_code == 422 and codes[4].json()["code"] == "HOLD_LIMIT"


def test_ready_reservation_expires_and_passes_on(
    client: TestClient, settings: Settings
):
    from uuid import UUID

    from lib_management.circulation.models import Reservation
    from lib_management.circulation.router import expire_ready_reservations

    reader, copy, checkout, _ = setup_loan(client)
    first, second = new_reader(client), new_reader(client)
    for who in (first, second):
        assert post(client, f"/readers/{who.json()['id']}/cards").status_code == 201
    holds = [
        post(
            client,
            "/reservations",
            {"readerId": who.json()["id"], "editionId": copy["edition_id"]},
        ).json()
        for who in (first, second)
    ]
    post(
        client,
        "/returns",
        {"loanItemId": checkout["items"][0]["loanItemId"], "condition": "GOOD"},
    )
    engine = create_engine_from_settings(settings)
    factory = create_session_factory(engine)
    with factory() as session, session.begin():
        ready = session.get(Reservation, UUID(holds[0]["id"]))
        assert ready is not None and ready.status == "READY"
        ready.ready_at = datetime.now(UTC) - timedelta(days=4)
        ready.ready_expires_at = datetime.now(UTC) - timedelta(minutes=1)
    with factory() as session, session.begin():
        assert expire_ready_reservations(session) >= 1
    with factory() as session:
        statuses = [
            session.get(Reservation, UUID(hold["id"])).status  # type: ignore[union-attr]
            for hold in holds
        ]
    engine.dispose()
    assert statuses == ["EXPIRED", "READY"]
