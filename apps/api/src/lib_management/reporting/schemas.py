"""Strict report filters and safe projections; internal payloads stay private."""

import uuid
from datetime import datetime, time, timedelta
from typing import Any, Literal, Self
from zoneinfo import ZoneInfo

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid", populate_by_name=True, from_attributes=True
    )


LIBRARY_ZONE = ZoneInfo("Asia/Ho_Chi_Minh")

# BM08 sections and the Lab 3 ReportJob.report_type domain; the first two are
# kept for requests made before BM08 was implemented.
ReportType = Literal[
    "LENDING_SUMMARY",
    "OVERDUE",
    "OVERVIEW",
    "LOAN_TREND",
    "INVENTORY",
    "TOP_BOOKS",
    "ACTIVE_READERS",
    "LOAN_CSV",
    "FINE_CSV",
]


class ReportFilters(Schema):
    from_: AwareDatetime = Field(alias="from")
    to: AwareDatetime
    granularity: Literal["day", "week", "month"] = "day"
    limit: int = Field(default=10, ge=1, le=100)

    @model_validator(mode="after")
    def interval(self) -> Self:
        if self.from_ >= self.to:
            raise ValueError("from must precede to")
        # QĐ13: Từ ngày ≤ Đến ngày ≤ ngày hiện tại (``to`` is the exclusive end,
        # so the last allowed value is the start of tomorrow in library time).
        tomorrow = datetime.now(LIBRARY_ZONE).date() + timedelta(days=1)
        if self.to > datetime.combine(tomorrow, time(), LIBRARY_ZONE):
            raise ValueError("to must not be after today (QĐ13)")
        return self


class ReportRequest(Schema):
    report_type: ReportType = Field(alias="reportType")
    filters: ReportFilters


class JobAccepted(Schema):
    job_id: uuid.UUID = Field(alias="jobId")
    status: Literal["QUEUED"] = "QUEUED"


class ReportView(Schema):
    id: uuid.UUID
    job_id: uuid.UUID
    report_type: str
    as_of: datetime
    artifact_id: uuid.UUID | None = None
    expires_at: datetime | None = None
    row_count: int | None = Field(default=None, ge=0)


class JobView(Schema):
    id: uuid.UUID
    job_type: str
    status: str
    attempt: int
    next_attempt_at: datetime | None = None
    last_error_code: str | None = None


class DownloadLink(Schema):
    download_url: str = Field(alias="downloadUrl")
    expires_at: datetime = Field(alias="expiresAt")


class Metrics(Schema):
    loan_items_issued: int = Field(ge=0)
    returns_received: int = Field(ge=0)
    distinct_borrowers: int = Field(ge=0)
    open_overdue_items: int = Field(ge=0)
    # BM08 §I; defaults keep artifacts produced before these existed readable.
    copies_in_stock: int = Field(default=0, ge=0)
    copies_on_loan: int = Field(default=0, ge=0)
    overdue_items: int = Field(default=0, ge=0)
    fines_assessed: str = Field(default="0", pattern="^[0-9]+$")


class ReportResult(Schema):
    report_id: uuid.UUID
    report_type: str
    as_of: datetime
    period: dict[str, Any]
    metrics: Metrics
    rows: list[dict[str, Any]]
    next_cursor: str | None = Field(default=None, alias="nextCursor")
