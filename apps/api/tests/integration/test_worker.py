import threading
import uuid

import pytest
from sqlalchemy import func, select, text, update

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
    assert runner.heartbeat(job_id, 1) is True
    assert Runner(session_factory, registry(), "w2").heartbeat(job_id, 1) is False


def test_long_handler_renews_lease_without_manual_heartbeat(session_factory):
    """A second worker must not reclaim a live handler that outlasts its lease."""
    make_job(session_factory)
    started = threading.Event()
    release = threading.Event()

    def handler(ctx):
        started.set()
        assert release.wait(5), "test did not release handler"

    runner = Runner(session_factory, registry(handler), "long-worker", lease_seconds=1)
    worker = threading.Thread(target=runner.run_once)
    worker.start()
    try:
        assert started.wait(2)
        # Deliberately outlast the initial one-second lease.
        threading.Event().wait(1.4)
        assert Runner(session_factory, registry(), "rival").claim() is None
    finally:
        release.set()
        worker.join(timeout=5)
    assert not worker.is_alive()
    job = jobs(session_factory)[0]
    assert (job.status, job.attempt) == ("SUCCEEDED", 1)


def test_expired_worker_cannot_resurrect_its_lease(session_factory):
    make_job(session_factory)
    runner = Runner(session_factory, registry(), "w1")
    job_id, *_ = runner.claim()
    with session_factory() as session, session.begin():
        session.execute(
            text("UPDATE job SET lease_until = now() - interval '1 second'")
        )
    assert runner.heartbeat(job_id, 1) is False


def test_stale_attempt_cannot_finish_reclaimed_job_with_same_owner(session_factory):
    make_job(session_factory)
    first = Runner(session_factory, registry(), "same-process")
    job_id, *_ = first.claim()
    with session_factory() as session, session.begin():
        session.execute(
            text("UPDATE job SET lease_until = now() - interval '1 second'")
        )
    second = Runner(session_factory, registry(), "same-process")
    assert second.claim()[2] == 2
    first._finish(job_id, 1, None)
    job = jobs(session_factory)[0]
    assert (job.status, job.attempt) == ("RUNNING", 2)


@pytest.mark.parametrize("action", ["heartbeat", "finish"])
def test_lease_expiring_while_waiting_for_lock_cannot_be_used(session_factory, action):
    import time

    job_id = make_job(session_factory)
    runner = Runner(session_factory, registry(), "blocked-worker", lease_seconds=1)
    runner.claim()
    results = []

    def use_lease():
        if action == "heartbeat":
            results.append(runner.heartbeat(job_id, 1))
        else:
            runner._finish(job_id, 1, None)

    with session_factory() as blocker, blocker.begin():
        blocker.execute(select(Job).where(Job.id == job_id).with_for_update())
        blocker_pid = blocker.scalar(text("SELECT pg_backend_pid()"))
        contender = threading.Thread(target=use_lease)
        contender.start()
        try:
            deadline = time.monotonic() + 1
            while True:
                with session_factory() as observer:
                    waiting = observer.scalar(
                        text(
                            "SELECT count(*) FROM pg_stat_activity "
                            "WHERE :pid = ANY(pg_blocking_pids(pid))"
                        ),
                        {"pid": blocker_pid},
                    )
                if waiting:
                    break
                assert time.monotonic() < deadline, "worker did not block before expiry"
                threading.Event().wait(0.01)
            # Cross expiry while the contender's DB operation remains blocked.
            blocker.execute(
                text(
                    "SELECT pg_sleep(GREATEST(0, EXTRACT(EPOCH FROM "
                    "(lease_until - clock_timestamp()))) + 0.1) FROM job WHERE id=:id"
                ),
                {"id": job_id},
            )
        finally:
            blocker.commit()
            contender.join(timeout=5)
    assert not contender.is_alive()
    if action == "heartbeat":
        assert results == [False]
    job = jobs(session_factory)[0]
    assert job.status == "RUNNING"
    with session_factory() as observer:
        assert observer.scalar(
            select(Job.lease_until < func.clock_timestamp()).where(Job.id == job_id)
        )


@pytest.mark.parametrize("failure", ["lost", "error"])
def test_failed_auto_renewal_cannot_publish_completion_or_leave_thread(
    session_factory, monkeypatch, failure
):
    job_id = make_job(session_factory)
    renewed = threading.Event()

    def handler(ctx):
        assert renewed.wait(2)

    runner = Runner(session_factory, registry(handler), "w1", lease_seconds=1)

    def failed_renewal(job_id, attempt):
        renewed.set()
        if failure == "error":
            raise RuntimeError("database unavailable")
        return False

    monkeypatch.setattr(runner, "heartbeat", failed_renewal)
    assert runner.run_once()
    assert jobs(session_factory)[0].status == "RUNNING"
    assert not any(t.name == f"lease-{job_id}" for t in threading.enumerate())


def test_stale_heartbeat_cannot_renew_new_attempt_with_same_owner(session_factory):
    job_id = make_job(session_factory)
    runner = Runner(session_factory, registry(), "same-process")
    runner.claim()
    with session_factory() as session, session.begin():
        session.execute(
            text("UPDATE job SET lease_until = now() - interval '1 second'")
        )
    assert Runner(session_factory, registry(), "same-process").claim()[2] == 2
    assert runner.heartbeat(job_id, 1) is False
