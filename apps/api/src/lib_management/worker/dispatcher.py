"""Outbox → Job. processed_at means "jobs created", not "delivered"."""

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, sessionmaker

from lib_management.platform.models import Job, OutboxEvent
from lib_management.worker.registry import Registry

BATCH_SIZE = 50


def dispatch_once(
    session_factory: sessionmaker[Session], registry: Registry, batch: int = BATCH_SIZE
) -> int:
    """Returns the number of events marked processed."""
    with session_factory() as session, session.begin():
        events = (
            session.execute(
                select(OutboxEvent)
                .where(OutboxEvent.processed_at.is_(None))
                .order_by(OutboxEvent.created_at, OutboxEvent.id)
                .limit(batch)
                .with_for_update(skip_locked=True)
            )
            .scalars()
            .all()
        )
        for event in events:
            for consumer in registry.consumers_for(event.event_type):
                session.execute(
                    insert(Job)
                    .values(
                        outbox_event_id=event.id,
                        dedupe_key=f"{event.id}:{consumer.name}",
                        job_type=consumer.job_type,
                        payload=event.payload,
                        status="QUEUED",
                    )
                    .on_conflict_do_nothing(index_elements=[Job.dedupe_key])
                )
            event.processed_at = func.now()
        return len(events)
