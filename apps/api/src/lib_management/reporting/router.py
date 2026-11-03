"""Authenticated polling, report snapshots and private export downloads."""

import json
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse

from lib_management.catalog.http import write
from lib_management.core.errors import Forbidden
from lib_management.core.pagination import PageParams, page_params
from lib_management.core.uow import UnitOfWork, get_uow
from lib_management.identity.auth import Principal, authenticated, require_permission
from lib_management.reporting import schemas, service
from lib_management.reporting.config import ReportingSettings
from lib_management.reporting.storage import ArtifactStorage, FileArtifactStorage

router = APIRouter(tags=["reports"])
Uow = Annotated[UnitOfWork, Depends(get_uow)]
ReportRead = Annotated[Principal, Depends(require_permission("report.read"))]
ExportCreate = Annotated[Principal, Depends(require_permission("export.create"))]
ExportDownload = Annotated[Principal, Depends(require_permission("export.download"))]
Authenticated = Annotated[Principal, Depends(authenticated)]
Paging = Annotated[PageParams, Depends(page_params)]
Key = Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)]


def artifact_storage() -> ArtifactStorage:
    return FileArtifactStorage(ReportingSettings().artifact_storage_root)


Storage = Annotated[ArtifactStorage, Depends(artifact_storage)]


def accepted(
    payload: schemas.ReportRequest,
    key: str,
    uow: UnitOfWork,
    actor: Principal,
    *,
    export: bool,
) -> JSONResponse:
    kind = "export" if export else "report"
    result = write(
        uow,
        actor,
        f"{kind}.request",
        lambda: service.request_report(
            uow.session, payload, actor.account_id, export=export
        ),
        key=key,
        payload=payload.model_dump(mode="json", by_alias=True),
        status=202,
    )
    job_id = json.loads(bytes(result.body))["jobId"]
    result.headers["Location"] = f"/api/v1/jobs/{job_id}"
    return result


@router.post(
    "/report-jobs",
    operation_id="post_report_jobs",
    status_code=202,
    response_model=schemas.JobAccepted,
)
def request_report(
    payload: schemas.ReportRequest, key: Key, uow: Uow, actor: ReportRead
) -> JSONResponse:
    return accepted(payload, key, uow, actor, export=False)


@router.post(
    "/export-jobs",
    operation_id="post_export_jobs",
    status_code=202,
    response_model=schemas.JobAccepted,
)
def request_export(
    payload: schemas.ReportRequest, key: Key, uow: Uow, actor: ExportCreate
) -> JSONResponse:
    return accepted(payload, key, uow, actor, export=True)


@router.get(
    "/report-jobs/{id}",
    operation_id="get_report_jobs_id",
    response_model=schemas.ReportView,
)
def get_report(
    id: uuid.UUID, uow: Uow, actor: ReportRead, response: Response
) -> schemas.ReportView:
    report, _ = service.owned_report(uow.session, id, actor.account_id)
    response.headers["Cache-Control"] = "no-store"
    return schemas.ReportView.model_validate(report)


@router.get("/jobs/{id}", operation_id="get_jobs_id", response_model=schemas.JobView)
def get_job(
    id: uuid.UUID, uow: Uow, actor: Authenticated, response: Response
) -> schemas.JobView:
    _, job = service.owned_report(uow.session, id, actor.account_id)
    permission = "export.create" if job.job_type == "export" else "report.read"
    if permission not in actor.permissions:
        raise Forbidden("PERMISSION_DENIED", f"Thiếu quyền {permission}")
    response.headers["Cache-Control"] = "no-store"
    return schemas.JobView.model_validate(job)


@router.get(
    "/report-jobs/{id}/result",
    operation_id="get_report_jobs_id_result",
    response_model=schemas.ReportResult,
)
def get_result(
    id: uuid.UUID,
    uow: Uow,
    actor: ReportRead,
    paging: Paging,
    storage: Storage,
    response: Response,
) -> dict[str, object]:
    response.headers["Cache-Control"] = "no-store"
    return service.result_page(uow.session, id, actor.account_id, paging, storage)


@router.get(
    "/export-jobs/{id}/download",
    operation_id="get_export_jobs_id_download",
    response_model=schemas.DownloadLink,
)
def download_link(
    id: uuid.UUID, request: Request, uow: Uow, actor: ExportDownload, response: Response
) -> schemas.DownloadLink:
    report, job = service.owned_report(uow.session, id, actor.account_id, export=True)
    service.ready_artifact(uow.session, report, job)
    assert report.expires_at is not None
    response.headers["Cache-Control"] = "no-store"
    return schemas.DownloadLink(
        downloadUrl=str(request.url_for("export_content", id=id)),
        expiresAt=report.expires_at,
    )


@router.get(
    "/export-jobs/{id}/content",
    operation_id="get_export_jobs_id_content",
    name="export_content",
    response_class=StreamingResponse,
)
def content(
    id: uuid.UUID, uow: Uow, actor: ExportDownload, storage: Storage
) -> StreamingResponse:
    report, job = service.owned_report(uow.session, id, actor.account_id, export=True)
    asset = service.ready_artifact(uow.session, report, job)
    data = service.artifact_bytes(storage, asset)
    return StreamingResponse(
        (data[index : index + 65536] for index in range(0, len(data), 65536)),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{report.report_type.lower()}-{report.id}.csv"'
            ),
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )
