"""Transaction boundary for audited synchronous HTTP commands."""

from collections.abc import Callable
from datetime import timedelta
from typing import Any

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from lib_management.core import idempotency
from lib_management.core.errors import Conflict
from lib_management.core.uow import UnitOfWork
from lib_management.identity.auth import Principal


def write(
    uow: UnitOfWork,
    actor: Principal,
    operation: str,
    command: Callable[[], Any],
    *,
    key: str | None = None,
    payload: Any = None,
    status: int = 200,
    location: str | None = None,
) -> JSONResponse:
    try:
        started = None
        if key is not None:
            started = idempotency.begin(
                uow.session,
                actor_id=actor.account_id,
                operation=operation,
                key=key,
                payload=payload,
                ttl=timedelta(hours=24),
            )
            if started.replay:
                body = started.response_body
                resource_id = body.get("id") if isinstance(body, dict) else None
                headers = (
                    {"Location": f"{location}/{resource_id}"}
                    if location and resource_id
                    else {}
                )
                return JSONResponse(
                    body, status_code=started.response_status, headers=headers
                )
        body = jsonable_encoder(command())
        if started is not None:
            idempotency.complete(uow.session, started, status, body)
        uow.commit()
        resource_id = body.get("id") if isinstance(body, dict) else None
        headers = (
            {"Location": f"{location}/{resource_id}"}
            if location and resource_id
            else {}
        )
        return JSONResponse(body, status_code=status, headers=headers)
    except IntegrityError as error:
        uow.rollback()
        raise Conflict(
            "Dữ liệu trùng hoặc tài nguyên tham chiếu đã thay đổi",
            code="RESOURCE_CONFLICT",
        ) from error
