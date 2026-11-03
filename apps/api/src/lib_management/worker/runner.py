"""Claim → run outside the transaction → record result, guarded by lease."""

import logging
import random
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

    def heartbeat(self, job_id: uuid.UUID) -> bool:
        with self.session_factory() as session, session.begin():
            result = cast(
                CursorResult[Any],
                session.execute(
                    update(Job)
                    .where(*self._owned(job_id))
                    .values(lease_until=func.now() + self.lease)
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
        context = JobContext(
            job_id=str(job_id),
            job_type=job_type,
            attempt=attempt,
            payload=payload,
            heartbeat=lambda: self.heartbeat(job_id),
        )
        try:
            handler(context)
        except JobError as error:
            self._finish(job_id, attempt, error)
        except Exception:
            logger.exception("Job handler crashed", extra={"job_id": str(job_id)})
            self._finish(job_id, attempt, JobError("HANDLER_EXCEPTION"))
        else:
            self._finish(job_id, attempt, None)
        return True

    def _owned(self, job_id: uuid.UUID) -> tuple[ColumnElement[bool], ...]:
        return (
            Job.id == job_id,
            Job.status == "RUNNING",
            Job.lease_owner == self.owner,
        )

    def _finish(self, job_id: uuid.UUID, attempt: int, error: JobError | None) -> None:
        with self.session_factory() as session, session.begin():
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
                    update(Job).where(*self._owned(job_id)).values(**values)
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
