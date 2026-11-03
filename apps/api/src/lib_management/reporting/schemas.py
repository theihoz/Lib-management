"""Strict report filters and safe projections; internal payloads stay private."""

import uuid
from datetime import datetime
from typing import Any, Literal, Self

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid", populate_by_name=True, from_attributes=True
    )


class ReportFilters(Schema):
    from_: AwareDatetime = Field(alias="from")
    to: AwareDatetime

    @model_validator(mode="after")
    def interval(self) -> Self:
        if self.from_ >= self.to:
            raise ValueError("from must precede to")
        return self


class ReportRequest(Schema):
    report_type: Literal["LENDING_SUMMARY", "OVERDUE"] = Field(alias="reportType")
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


class ReportResult(Schema):
    report_id: uuid.UUID
    report_type: str
    as_of: datetime
    period: dict[str, Any]
    metrics: Metrics
    rows: list[dict[str, Any]]
    next_cursor: str | None = Field(default=None, alias="nextCursor")
