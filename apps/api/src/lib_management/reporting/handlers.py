"""Report handler materializes a consistent worker-start database snapshot."""

import json
import uuid
from datetime import timedelta

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session, sessionmaker

from lib_management.core import audit
from lib_management.reporting.config import ReportingSettings
from lib_management.reporting.models import MediaAsset, ReportJob
from lib_management.reporting.service import csv_bytes, snapshot
from lib_management.reporting.storage import (
    ArtifactStorage,
    FileArtifactStorage,
    checksum,
)
from lib_management.worker.registry import Handler, JobContext, JobError


def report_handler(
    session_factory: sessionmaker[Session],
    storage: ArtifactStorage,
    retention: timedelta,
) -> Handler:
    def run(context: JobContext) -> None:
        try:
            report_id = uuid.UUID(str(context.payload["report_id"]))
            job_id = uuid.UUID(context.job_id)
        except (KeyError, ValueError, TypeError) as error:
            raise JobError("INVALID_REPORT_PAYLOAD", permanent=True) from error
        key: str | None = None
        try:
            with session_factory() as session:
                session.connection(
                    execution_options={"isolation_level": "REPEATABLE READ"}
                )
                session.execute(text("SET LOCAL statement_timeout = '30s'"))
                # This query establishes the database snapshot and its server time.
                as_of = session.execute(
                    select(func.transaction_timestamp(), func.pg_current_snapshot())
                ).one()[0]
                report = session.scalar(
                    select(ReportJob)
                    .where(ReportJob.id == report_id, ReportJob.job_id == job_id)
                    .with_for_update()
                )
                if report is None:
                    raise JobError("REPORT_NOT_FOUND", permanent=True)
                if report.artifact_id is not None:
                    # A reclaimed job may already have a committed artifact.
                    return
                result = snapshot(session, report, as_of)
                export = context.job_type == "export"
                data = (
                    csv_bytes(result)
                    if export
                    else json.dumps(
                        result, ensure_ascii=False, separators=(",", ":")
                    ).encode("utf-8")
                )
                if not context.heartbeat():
                    raise JobError("REPORT_LEASE_LOST")
                key = storage.put(data)
                asset = MediaAsset(
                    object_key=key,
                    mime_type="text/csv" if export else "application/json",
                    byte_size=len(data),
                    sha256=checksum(data),
                    visibility="PRIVATE",
                    status="READY",
                    uploaded_by=report.requested_by,
                )
                session.add(asset)
                session.flush()
                report.as_of = as_of
                report.artifact_id = asset.id
                report.expires_at = as_of + retention
                report.row_count = len(result["rows"])
                audit.record(
                    session,
                    action="export.materialized" if export else "report.materialized",
                    target_type="report_job",
                    target_id=report.id,
                    actor_type="SYSTEM",
                    outcome="SUCCESS",
                    metadata={"row_count": report.row_count},
                )
                if not context.heartbeat():
                    raise JobError("REPORT_LEASE_LOST")
                session.commit()
                key = None
        finally:
            if key is not None:
                storage.delete(key)

    return run


def configured_handler(context: JobContext) -> None:
    # Lazy configuration keeps worker registry construction side-effect free.
    from lib_management.config import Settings
    from lib_management.db import create_engine_from_settings, create_session_factory

    settings = Settings()  # type: ignore[call-arg]  # Loaded from environment.
    options = ReportingSettings()
    engine = create_engine_from_settings(settings)
    try:
        handler = report_handler(
            create_session_factory(engine),
            FileArtifactStorage(options.artifact_storage_root),
            timedelta(hours=options.report_artifact_retention_hours),
        )
        handler(context)
    finally:
        engine.dispose()
