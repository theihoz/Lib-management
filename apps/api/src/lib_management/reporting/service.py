"""Durable report requests, snapshot aggregation and scoped artifact reads."""

import csv
import io
import json
import uuid
from datetime import UTC, datetime
from typing import Any, cast

from fastapi.encoders import jsonable_encoder
from sqlalchemy import or_, select, text
from sqlalchemy.orm import Session

from lib_management.core import audit
from lib_management.core.errors import (
    AppError,
    Conflict,
    NotFound,
    ServiceUnavailable,
    ValidationFailed,
)
from lib_management.core.pagination import PageParams, encode_cursor
from lib_management.platform.models import Job
from lib_management.reporting.models import MediaAsset, ReportJob
from lib_management.reporting.schemas import ReportRequest
from lib_management.reporting.storage import ArtifactStorage, checksum

LIBRARY_TIMEZONE = "Asia/Ho_Chi_Minh"


def request_report(
    session: Session, payload: ReportRequest, actor_id: uuid.UUID, *, export: bool
) -> dict[str, Any]:
    report_id, job_id = uuid.uuid4(), uuid.uuid4()
    job_type = "export" if export else "report"
    job = Job(
        id=job_id,
        dedupe_key=f"{job_type}:{report_id}",
        job_type=job_type,
        payload={"report_id": str(report_id)},
        status="QUEUED",
    )
    session.add(job)
    session.flush()
    report = ReportJob(
        id=report_id,
        job_id=job_id,
        requested_by=actor_id,
        report_type=payload.report_type,
        filter_snapshot=payload.filters.model_dump(mode="json", by_alias=True),
        as_of=datetime.now(UTC),
    )
    session.add(report)
    audit.record(
        session,
        action=f"{job_type}.request",
        target_type="report_job",
        target_id=report_id,
        actor_id=actor_id,
        permission_code="export.create" if export else "report.read",
        outcome="SUCCESS",
        metadata={"report_type": payload.report_type},
    )
    session.flush()
    return {"jobId": str(job_id), "status": "QUEUED"}


def owned_report(
    session: Session,
    identity: uuid.UUID,
    actor_id: uuid.UUID,
    *,
    export: bool | None = None,
) -> tuple[ReportJob, Job]:
    statement = (
        select(ReportJob, Job)
        .join(Job, Job.id == ReportJob.job_id)
        .where(
            or_(ReportJob.id == identity, ReportJob.job_id == identity),
            ReportJob.requested_by == actor_id,
            Job.job_type.in_(["report", "export"]),
        )
    )
    if export is not None:
        statement = statement.where(Job.job_type == ("export" if export else "report"))
    found = session.execute(statement).one_or_none()
    if found is None:
        raise NotFound()
    return found[0], found[1]


def ready_artifact(session: Session, report: ReportJob, job: Job) -> MediaAsset:
    if job.status != "SUCCEEDED":
        raise Conflict("Tác vụ chưa tạo kết quả thành công", code="REPORT_NOT_READY")
    if report.expires_at is None or report.expires_at <= datetime.now(UTC):
        raise AppError(410, "ARTIFACT_EXPIRED", "Kết quả báo cáo đã hết hạn")
    asset = session.get(MediaAsset, report.artifact_id) if report.artifact_id else None
    if asset is None or asset.status != "READY" or asset.visibility != "PRIVATE":
        raise ServiceUnavailable("Tệp kết quả chưa sẵn sàng")
    return asset


def artifact_bytes(storage: ArtifactStorage, asset: MediaAsset) -> bytes:
    try:
        data = storage.get(asset.object_key)
    except (OSError, ValueError) as error:
        raise ServiceUnavailable("Không đọc được tệp kết quả") from error
    if len(data) != asset.byte_size or checksum(data) != asset.sha256:
        raise ServiceUnavailable("Tệp kết quả không toàn vẹn")
    return data


def result_page(
    session: Session,
    identity: uuid.UUID,
    actor_id: uuid.UUID,
    params: PageParams,
    storage: ArtifactStorage,
) -> dict[str, Any]:
    report, job = owned_report(session, identity, actor_id, export=False)
    asset = ready_artifact(session, report, job)
    try:
        result: dict[str, Any] = json.loads(artifact_bytes(storage, asset))
    except (ValueError, TypeError) as error:
        raise ServiceUnavailable("Kết quả báo cáo không hợp lệ") from error
    index = 0
    if params.cursor is not None:
        if params.cursor.id != report.id or len(params.cursor.k) != 1:
            raise ValidationFailed("Cursor không thuộc báo cáo này")
        try:
            index = int(params.cursor.k[0])
        except ValueError as error:
            raise ValidationFailed("Cursor báo cáo không hợp lệ") from error
        if index < 0:
            raise ValidationFailed("Cursor báo cáo không hợp lệ")
    rows = result["rows"]
    result["rows"] = rows[index : index + params.limit]
    next_index = index + params.limit
    result["nextCursor"] = (
        encode_cursor([str(next_index)], report.id) if next_index < len(rows) else None
    )
    return result


METRICS_SQL = text("""
SELECT
 (SELECT count(*) FROM loan_item WHERE issued_at >= :from_at AND issued_at < :to_at)
AS loan_items_issued,
 (SELECT count(*) FROM return_event WHERE returned_at >= :from_at AND returned_at <
:to_at AND return_kind = 'RETURNED') AS returns_received,
 (SELECT count(DISTINCT l.reader_id) FROM loan l JOIN loan_item i ON i.loan_id =
l.id WHERE i.issued_at >= :from_at AND i.issued_at < :to_at) AS distinct_borrowers,
 (SELECT count(*) FROM loan_item WHERE closed_at IS NULL AND due_at < :as_of AND
due_at >= :from_at AND due_at < :to_at) AS open_overdue_items
""")
LENDING_SQL = text("""
WITH issued AS (
 SELECT c.edition_id, count(*) AS issued_count FROM loan_item i
 JOIN book_copy c ON c.id = i.copy_id
 WHERE i.issued_at >= :from_at AND i.issued_at < :to_at GROUP BY c.edition_id
), returned AS (
 SELECT c.edition_id, count(*) AS returned_count FROM return_event r
 JOIN loan_item i ON i.id = r.loan_item_id JOIN book_copy c ON c.id = i.copy_id
 WHERE r.returned_at >= :from_at AND r.returned_at < :to_at AND r.return_kind =
'RETURNED' GROUP BY c.edition_id
)
SELECT e.id AS edition_id, e.title, coalesce(i.issued_count, 0) AS issued_count,
 coalesce(r.returned_count, 0) AS returned_count
FROM book_edition e LEFT JOIN issued i ON i.edition_id = e.id LEFT JOIN returned r
ON r.edition_id = e.id
WHERE i.edition_id IS NOT NULL OR r.edition_id IS NOT NULL ORDER BY e.id
""")
OVERDUE_SQL = text("""
SELECT i.id AS loan_item_id, l.loan_no, r.reader_code, r.full_name, c.barcode,
i.due_at,
 greatest(0, (:as_of AT TIME ZONE 'Asia/Ho_Chi_Minh')::date - (i.due_at AT TIME ZONE
'Asia/Ho_Chi_Minh')::date) AS late_days
FROM loan_item i JOIN loan l ON l.id = i.loan_id JOIN reader r ON r.id = l.reader_id
JOIN book_copy c ON c.id = i.copy_id
WHERE i.closed_at IS NULL AND i.due_at < :as_of AND i.due_at >= :from_at AND
i.due_at < :to_at ORDER BY i.due_at, i.id
""")


def snapshot(session: Session, report: ReportJob, as_of: datetime) -> dict[str, Any]:
    params = {
        "from_at": datetime.fromisoformat(report.filter_snapshot["from"]),
        "to_at": datetime.fromisoformat(report.filter_snapshot["to"]),
        "as_of": as_of,
    }
    metrics = dict(session.execute(METRICS_SQL, params).mappings().one())
    rows = [
        dict(row)
        for row in session.execute(
            LENDING_SQL if report.report_type == "LENDING_SUMMARY" else OVERDUE_SQL,
            params,
        ).mappings()
    ]
    return cast(
        dict[str, Any],
        jsonable_encoder(
            {
                "report_id": report.id,
                "report_type": report.report_type,
                "as_of": as_of,
                "period": {**report.filter_snapshot, "timezone": LIBRARY_TIMEZONE},
                "metrics": metrics,
                "rows": rows,
            }
        ),
    )


def csv_cell(value: Any) -> Any:
    if isinstance(value, str):
        # Spreadsheet applications trim control/whitespace before formulas.
        significant = value.lstrip("".join(chr(i) for i in range(33)))
        if significant.startswith(("=", "+", "-", "@")):
            return "'" + value
    return value


def csv_bytes(result: dict[str, Any]) -> bytes:
    fields = (
        ["edition_id", "title", "issued_count", "returned_count"]
        if result["report_type"] == "LENDING_SUMMARY"
        else [
            "loan_item_id",
            "loan_no",
            "reader_code",
            "full_name",
            "barcode",
            "due_at",
            "late_days",
        ]
    )
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\r\n")
    writer.writerow(fields)
    for row in result["rows"]:
        writer.writerow([csv_cell(row[field]) for field in fields])
    return output.getvalue().encode("utf-8")
