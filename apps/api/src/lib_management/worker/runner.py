"""Claim → run outside the transaction → record result, guarded by lease."""

import logging
import random
import threading
import uuid
from datetime import timedelta
from typing import Any, cast

from sqlalchemy import ColumnElement, CursorResult, and_, func, or_, select, update
from sqlalchemy.orm import Session, sessionmaker

from lib_management.core import audit
from lib_management.platform.models import Job
from lib_management.worker.registry import JobContext, JobError, Registry

logger = logging.getLogger(__name__)
MAX_BACKOFF_SECONDS = 60.0


def backoff_seconds(attempt: int, rng: random.Random | None = None) -> float:
    """1, 2, 4, 8 … seconds capped at 60, plus up to 25% jitter."""
    base = min(2.0 ** max(attempt - 1, 0), MAX_BACKOFF_SECONDS)
    jitter = (rng or random).uniform(0, base * 0.25)
    return min(base + jitter, MAX_BACKOFF_SECONDS)


class Runner:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
        registry: Registry,
        owner: str,
        lease_seconds: int = 60,
        max_attempts: int = 5,
    ) -> None:
        self.session_factory = session_factory
        self.registry = registry
        self.owner = owner[:100]
        self.lease = timedelta(seconds=lease_seconds)
        self.heartbeat_interval = min(20.0, lease_seconds / 3)
        self.max_attempts = max_attempts

    def claim(self) -> tuple[uuid.UUID, str, int, dict[str, object]] | None:
        with self.session_factory() as session, session.begin():
            job = session.execute(
                select(Job)
                .where(
                    or_(
                        and_(
                            Job.status == "QUEUED",
                            or_(
                                Job.next_attempt_at.is_(None),
                                Job.next_attempt_at <= func.now(),
                            ),
                        ),
                        and_(Job.status == "RUNNING", Job.lease_until < func.now()),
                    )
                )
                .order_by(Job.created_at, Job.id)
                .limit(1)
                .with_for_update(skip_locked=True)
            ).scalar_one_or_none()
            if job is None:
                return None
            job.status = "RUNNING"
            job.lease_owner = self.owner
            job.lease_until = func.now() + self.lease
            job.attempt = job.attempt + 1
            session.flush()
            session.refresh(job)
            return job.id, job.job_type, job.attempt, dict(job.payload)

    def heartbeat(self, job_id: uuid.UUID, attempt: int) -> bool:
        with self.session_factory() as session, session.begin():
            self._lock_job(session, job_id)
            result = cast(
                CursorResult[Any],
                session.execute(
                    update(Job)
                    .where(*self._owned(job_id, attempt))
                    .values(lease_until=func.clock_timestamp() + self.lease)
                ),
            )
            return result.rowcount == 1

    def run_once(self) -> bool:
        """Processes at most one job; returns False when the queue is empty."""
        claimed = self.claim()
        if claimed is None:
            return False
        job_id, job_type, attempt, payload = claimed
        handler = self.registry.handlers.get(job_type)
        if handler is None:
            self._finish(job_id, attempt, JobError("UNKNOWN_JOB_TYPE", permanent=True))
            return True
        stop = threading.Event()
        lost = threading.Event()

        def renew() -> bool:
            if lost.is_set():
                return False
            owned = self.heartbeat(job_id, attempt)
            if not owned:
                lost.set()
            return owned

        def keep_lease() -> None:
            while not stop.wait(self.heartbeat_interval):
                try:
                    if not renew():
                        return
                except Exception as error:
                    lost.set()
                    logger.warning(
                        "Lease renewal failed",
                        extra={
                            "job_id": str(job_id),
                            "error_type": type(error).__name__,
                        },
                    )
                    return

        context = JobContext(
            job_id=str(job_id),
            job_type=job_type,
            attempt=attempt,
            payload=payload,
            heartbeat=renew,
        )
        keeper = threading.Thread(
            target=keep_lease, name=f"lease-{job_id}", daemon=True
        )
        keeper.start()
        failure: JobError | None = None
        try:
            handler(context)
        except JobError as error:
            failure = error
        except Exception:
            logger.exception("Job handler crashed", extra={"job_id": str(job_id)})
            failure = JobError("HANDLER_EXCEPTION")
        finally:
            stop.set()
            keeper.join()
        if not lost.is_set():
            self._finish(job_id, attempt, failure)
        return True

    def _owned(
        self, job_id: uuid.UUID, attempt: int
    ) -> tuple[ColumnElement[bool], ...]:
        return (
            Job.id == job_id,
            Job.status == "RUNNING",
            Job.lease_owner == self.owner,
            Job.lease_until > func.clock_timestamp(),
            Job.attempt == attempt,
        )

    @staticmethod
    def _lock_job(session: Session, job_id: uuid.UUID) -> None:
        # Evaluate the expiry guard only AFTER acquiring the row lock. An
        # UPDATE predicate alone could be evaluated before waiting on a lock.
        session.execute(
            select(Job.id).where(Job.id == job_id).with_for_update()
        ).scalar_one_or_none()

    def _finish(self, job_id: uuid.UUID, attempt: int, error: JobError | None) -> None:
        with self.session_factory() as session, session.begin():
            self._lock_job(session, job_id)
            values: dict[str, object] = {"lease_owner": None, "lease_until": None}
            if error is None:
                values |= {"status": "SUCCEEDED", "last_error_code": None}
            elif error.permanent or attempt >= self.max_attempts:
                values |= {"status": "DEAD", "last_error_code": error.code}
            else:
                delay = timedelta(seconds=backoff_seconds(attempt))
                values |= {
                    "status": "QUEUED",
                    "last_error_code": error.code,
                    "next_attempt_at": func.now() + delay,
                }
            result = cast(
                CursorResult[Any],
                session.execute(
                    update(Job).where(*self._owned(job_id, attempt)).values(**values)
                ),
            )
            if result.rowcount != 1:
                # Lease expired and another worker took over; its result wins.
                logger.warning(
                    "Lost lease before finishing", extra={"job_id": str(job_id)}
                )
                return
            if values["status"] == "DEAD":
                audit.record(
                    session,
                    action="job.dead",
                    target_type="job",
                    target_id=job_id,
                    outcome="FAILED",
                    actor_type="SYSTEM",
                    metadata={
                        "error_code": values["last_error_code"],
                        "attempt": attempt,
                    },
                )
