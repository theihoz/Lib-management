import threading
from datetime import timedelta

import pytest
from sqlalchemy import func, select

from lib_management.core import idempotency
from lib_management.core.errors import Conflict
from lib_management.identity.models import Account, Role
from lib_management.platform.models import IdempotencyRecord

TTL = timedelta(hours=24)


@pytest.fixture
def actor(session_factory):
    with session_factory() as session, session.begin():
        account = Account(issuer="i", subject="s", display_name="x", status="ACTIVE")
        session.add(account)
    return account.id


def command(session_factory, actor, key, payload, fail=False):
    """Simulates a business command creating one Role per execution."""
    with session_factory() as session, session.begin():
        started = idempotency.begin(
            session,
            actor_id=actor,
            operation="role.create",
            key=key,
            payload=payload,
            ttl=TTL,
        )
        if started.replay:
            return started.response_status, started.response_body
        session.add(Role(code=payload["code"], name="n"))
        if fail:
            raise RuntimeError("business failure")
        body = {"code": payload["code"]}
        idempotency.complete(session, started, 201, body)
        return 201, body


def roles(session_factory):
    with session_factory() as session:
        return session.execute(select(func.count()).select_from(Role)).scalar_one()


def test_same_key_same_payload_replays(session_factory, actor):
    first = command(session_factory, actor, "k1", {"code": "A"})
    second = command(session_factory, actor, "k1", {"code": "A"})
    assert first == second == (201, {"code": "A"})
    assert roles(session_factory) == 1


def test_hash_is_order_independent():
    assert idempotency.payload_hash({"a": 1, "b": 2}) == idempotency.payload_hash(
        {"b": 2, "a": 1}
    )


def test_same_key_different_payload_conflicts(session_factory, actor):
    command(session_factory, actor, "k1", {"code": "A"})
    with pytest.raises(Conflict) as error:
        command(session_factory, actor, "k1", {"code": "B"})
    assert error.value.code == "IDEMPOTENCY_MISMATCH"


def test_failed_command_leaves_no_record(session_factory, actor):
    with pytest.raises(RuntimeError):
        command(session_factory, actor, "k1", {"code": "A"}, fail=True)
    with session_factory() as session:
        assert session.execute(select(IdempotencyRecord)).first() is None
    assert command(session_factory, actor, "k1", {"code": "A"})[0] == 201


def test_concurrent_duplicate_is_in_progress(session_factory, actor):
    holding = threading.Event()
    release = threading.Event()

    def slow():
        with session_factory() as session, session.begin():
            idempotency.begin(
                session,
                actor_id=actor,
                operation="role.create",
                key="k1",
                payload={"code": "A"},
                ttl=TTL,
            )
            holding.set()
            release.wait(5)

    thread = threading.Thread(target=slow)
    thread.start()
    try:
        assert holding.wait(5)
        with pytest.raises(Conflict) as error:
            command(session_factory, actor, "k1", {"code": "A"})
        assert error.value.code == "IDEMPOTENCY_IN_PROGRESS"
        assert error.value.headers == {"Retry-After": "1"}
    finally:
        release.set()
        thread.join()


def test_expired_record_is_replaced(session_factory, actor):
    command(session_factory, actor, "k1", {"code": "A"})
    with session_factory() as session, session.begin():
        record = session.execute(select(IdempotencyRecord)).scalar_one()
        record.expires_at = record.created_at - timedelta(seconds=1)
    assert command(session_factory, actor, "k1", {"code": "B"})[0] == 201
