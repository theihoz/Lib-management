import threading
import uuid

import pytest
from sqlalchemy import select, text, update

from lib_management.core import outbox
from lib_management.platform.models import AuditLog, Job, OutboxEvent
from lib_management.worker.dispatcher import dispatch_once
from lib_management.worker.registry import Consumer, JobError, Registry
from lib_management.worker.runner import Runner

EVENT = "test.happened.v1"


def registry(handler=lambda ctx: None, consumers=("a", "b")):
    return Registry(
        handlers={"test.v1": handler},
        consumers={EVENT: tuple(Consumer(name, "test.v1") for name in consumers)},
    )


def publish(session_factory, data=None):
    with session_factory() as session, session.begin():
        return outbox.publish(
            session,
            aggregate_type="thing",
            aggregate_id=uuid.uuid4(),
            event_type=EVENT,
            data=data or {"x": 1},
        )


def jobs(session_factory):
    with session_factory() as session:
        return session.execute(select(Job).order_by(Job.dedupe_key)).scalars().all()


def test_envelope_v1(session_factory):
    event_id = publish(session_factory)
    with session_factory() as session:
        payload = session.get(OutboxEvent, event_id).payload
    assert payload["schemaVersion"] == 1
    assert payload["eventId"] == str(event_id)
    assert payload["eventType"] == EVENT
    assert payload["occurredAt"].endswith("Z")
    assert payload["data"] == {"x": 1}


def test_dispatch_creates_one_job_per_consumer_and_is_idempotent(session_factory):
    event_id = publish(session_factory)
    assert dispatch_once(session_factory, registry()) == 1
    # Simulate a crash before processed_at was visible: dispatch again.
    with session_factory() as session, session.begin():
        session.execute(update(OutboxEvent).values(processed_at=None))
    assert dispatch_once(session_factory, registry()) == 1
    keys = [job.dedupe_key for job in jobs(session_factory)]
    assert keys == [f"{event_id}:a", f"{event_id}:b"]
    assert dispatch_once(session_factory, registry()) == 0


def make_job(session_factory, job_type="test.v1", **values):
    with session_factory() as session, session.begin():
        job = Job(
            dedupe_key=str(uuid.uuid4()),
            job_type=job_type,
            payload={},
            status="QUEUED",
            **values,
        )
        session.add(job)
    return job.id


def test_success(session_factory):
    job_id = make_job(session_factory)
    runner = Runner(session_factory, registry(), "w1")
    assert runner.run_once() is True
    assert runner.run_once() is False
    job = jobs(session_factory)[0]
    assert (job.id, job.status, job.attempt, job.lease_owner) == (
        job_id,
        "SUCCEEDED",
        1,
        None,
    )


def test_two_workers_never_claim_same_job(session_factory):
    for _ in range(10):
        make_job(session_factory)
    seen: list[str] = []
    lock = threading.Lock()

    def handler(ctx):
        with lock:
            seen.append(ctx.job_id)

    def work(owner):
        runner = Runner(session_factory, registry(handler), owner)
        while runner.run_once():
            pass

    threads = [threading.Thread(target=work, args=(f"w{i}",)) for i in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len(seen) == len(set(seen)) == 10
    assert {job.status for job in jobs(session_factory)} == {"SUCCEEDED"}


def test_expired_lease_is_reclaimed_and_old_owner_cannot_finish(session_factory):
    make_job(session_factory)
    first = Runner(session_factory, registry(), "w1")
    job_id, *_ = first.claim()
    with session_factory() as session, session.begin():
        session.execute(
            text("UPDATE job SET lease_until = now() - interval '1 second'")
        )
    second = Runner(session_factory, registry(), "w2")
    assert second.run_once() is True
    first._finish(job_id, 1, JobError("LATE"))  # stale owner: ignored
    job = jobs(session_factory)[0]
    assert (job.status, job.attempt, job.last_error_code) == ("SUCCEEDED", 2, None)


def test_retry_with_backoff_then_dead_after_max_attempts(session_factory):
    make_job(session_factory)

    def failing(ctx):
        raise JobError("SMTP_TIMEOUT")

    runner = Runner(session_factory, registry(failing), "w1", max_attempts=3)
    assert runner.run_once() is True
    job = jobs(session_factory)[0]
    assert (job.status, job.attempt, job.last_error_code) == (
        "QUEUED",
        1,
        "SMTP_TIMEOUT",
    )
    assert job.next_attempt_at is not None
    assert runner.run_once() is False  # not due yet
    for _ in range(2):
        with session_factory() as session, session.begin():
            session.execute(text("UPDATE job SET next_attempt_at = now()"))
        assert runner.run_once() is True
    job = jobs(session_factory)[0]
    assert (job.status, job.attempt) == ("DEAD", 3)
    with session_factory() as session:
        entry = session.execute(select(AuditLog)).scalar_one()
    assert (entry.action, entry.outcome, entry.actor_type) == (
        "job.dead",
        "FAILED",
        "SYSTEM",
    )


@pytest.mark.parametrize(
    ("job_type", "handler", "code"),
    [
        ("unknown.v1", lambda ctx: None, "UNKNOWN_JOB_TYPE"),
        (
            "test.v1",
            lambda ctx: (_ for _ in ()).throw(JobError("BAD", permanent=True)),
            "BAD",
        ),
    ],
)
def test_permanent_failures_go_dead_immediately(
    session_factory, job_type, handler, code
):
    make_job(session_factory, job_type=job_type)
    Runner(session_factory, registry(handler), "w1").run_once()
    job = jobs(session_factory)[0]
    assert (job.status, job.attempt, job.last_error_code) == ("DEAD", 1, code)


def test_crashing_handler_is_retried(session_factory):
    make_job(session_factory)

    def crash(ctx):
        raise RuntimeError("password=hunter2")

    Runner(session_factory, registry(crash), "w1").run_once()
    job = jobs(session_factory)[0]
    assert (job.status, job.last_error_code) == ("QUEUED", "HANDLER_EXCEPTION")


def test_heartbeat_extends_own_lease_only(session_factory):
    make_job(session_factory)
    runner = Runner(session_factory, registry(), "w1")
    job_id, *_ = runner.claim()
    assert runner.heartbeat(job_id) is True
    assert Runner(session_factory, registry(), "w2").heartbeat(job_id) is False
