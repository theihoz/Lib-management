import asyncio
import uuid

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from lib_management import migrate
from lib_management.db import DatabaseProbe


def test_round_trip_from_empty(settings, engine):
    migrate.downgrade(settings, "base")
    assert set(inspect(engine).get_table_names()) <= {"alembic_version"}
    migrate.upgrade(settings)
    tables = set(inspect(engine).get_table_names())
    assert {"account", "role", "permission", "job", "audit_log"} <= tables
    with engine.connect() as connection:
        version = connection.execute(text("SELECT version_num FROM alembic_version"))
        assert version.scalar_one() == migrate.head_revision()


@pytest.mark.parametrize(
    "statement",
    [
        "INSERT INTO account (id, issuer, subject, display_name, status) "
        "VALUES (:a, 'i', 's', 'x', 'ACTIVE'), (:b, 'i', 's', 'y', 'ACTIVE')",
        "INSERT INTO account (id, issuer, subject, display_name, status) "
        "VALUES (:a, 'i', 's', 'x', 'UNKNOWN')",
        "INSERT INTO job (id, dedupe_key, job_type, payload, status, attempt) "
        "VALUES (:a, 'k', 't', '{}', 'QUEUED', -1)",
        "INSERT INTO job (id, dedupe_key, job_type, payload, status) "
        "VALUES (:a, 'k', 't', '{}', 'QUEUED'), (:b, 'k', 't', '{}', 'QUEUED')",
        "INSERT INTO job (id, dedupe_key, job_type, payload, status) "
        "VALUES (:a, 'k', 't', '{}', 'WAITING')",
        "INSERT INTO audit_log (id, actor_type, action, target_type, request_id, "
        "outcome, metadata) VALUES (:a, 'ROBOT', 'x', 't', 'r', 'SUCCESS', '{}')",
    ],
    ids=[
        "dup-issuer-subject",
        "bad-status",
        "negative-attempt",
        "dup-dedupe",
        "bad-job-status",
        "bad-actor-type",
    ],
)
def test_constraints_reject_invalid_rows(session_factory, statement):
    with pytest.raises(IntegrityError), session_factory() as session:
        session.execute(text(statement), {"a": uuid.uuid4(), "b": uuid.uuid4()})
        session.flush()


def test_defaults(session_factory):
    with session_factory() as session, session.begin():
        row = session.execute(
            text(
                "INSERT INTO account (id, issuer, subject, display_name, status) "
                "VALUES (:a, 'i', 's', 'x', 'ACTIVE') "
                "RETURNING auth_version, created_at"
            ),
            {"a": uuid.uuid4()},
        ).one()
    assert row.auth_version == 1
    assert row.created_at.tzinfo is not None


def test_readiness_requires_head_revision(settings):
    probe = DatabaseProbe(settings, expected_revision=migrate.head_revision())
    assert asyncio.run(probe.check()) is True
    migrate.downgrade(settings, "0001_identity")
    try:
        assert asyncio.run(probe.check()) is False
    finally:
        migrate.upgrade(settings)
    migrate.downgrade(settings, "base")
    try:
        assert asyncio.run(probe.check()) is False
    finally:
        migrate.upgrade(settings)
