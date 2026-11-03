"""Staff reader and card endpoints; authorization is rechecked per request."""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, Query
from fastapi.responses import JSONResponse

from lib_management.catalog.http import write
from lib_management.catalog.service import get, page
from lib_management.core.pagination import Page, PageParams, page_params
from lib_management.core.uow import UnitOfWork, get_uow
from lib_management.identity.auth import (
    Principal,
    require_permission,
    staff_reader_scope,
)
from lib_management.readers import models, schemas, service

router = APIRouter(tags=["readers"])
Uow = Annotated[UnitOfWork, Depends(get_uow)]
Read = Annotated[Principal, Depends(require_permission("reader.read"))]
Write = Annotated[Principal, Depends(require_permission("reader.write"))]
Issue = Annotated[Principal, Depends(require_permission("card.issue"))]
Eligible = Annotated[Principal, Depends(require_permission("eligibility.read"))]
Paging = Annotated[PageParams, Depends(page_params)]
Key = Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)]


@router.get("/readers", operation_id="get_readers", response_model=Page[schemas.Reader])
def list_readers(
    uow: Uow,
    actor: Read,
    paging: Paging,
    query: Annotated[str | None, Query(max_length=300)] = None,
) -> dict[str, Any]:
    from lib_management.core.errors import Forbidden

    if not staff_reader_scope(actor):
        raise Forbidden("PERMISSION_DENIED", "Danh sách độc giả dành cho nhân viên")
    return page(uow.session, models.Reader, paging, query)


@router.get("/readers/lookup", operation_id="get_readers_lookup")
def lookup_reader(
    uow: Uow,
    actor: Read,
    query: Annotated[str | None, Query(min_length=1, max_length=200)] = None,
    cardNo: Annotated[str | None, Query(min_length=1, max_length=64)] = None,
) -> dict[str, Any]:
    from sqlalchemy import or_, select

    from lib_management.circulation.service import view
    from lib_management.core.errors import Forbidden, ValidationFailed

    if not staff_reader_scope(actor):
        raise Forbidden("PERMISSION_DENIED", "Tra cứu độc giả dành cho nhân viên")
    if not query and not cardNo:
        raise ValidationFailed("Nhập mã độc giả, tên hoặc số thẻ")
    statement = select(models.Reader)
    if cardNo:
        statement = statement.join(
            models.ReaderCard, models.ReaderCard.reader_id == models.Reader.id
        ).where(models.ReaderCard.card_no == cardNo)
    elif query:
        escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        statement = statement.where(
            or_(
                models.Reader.reader_code == query,
                models.Reader.full_name.ilike(f"%{escaped}%", escape="\\"),
            )
        )
    rows = uow.session.scalars(
        statement.order_by(models.Reader.reader_code, models.Reader.id).limit(20)
    ).all()
    return {"data": [view(row) for row in rows], "nextCursor": None}


@router.get(
    "/readers/{id}", operation_id="get_readers_id", response_model=schemas.Reader
)
def get_reader(id: uuid.UUID, uow: Uow, actor: Read) -> models.Reader:
    from lib_management.core.errors import NotFound

    if not staff_reader_scope(actor) and actor.account.reader_id != id:
        raise NotFound()
    return get(uow.session, models.Reader, id)


@router.post(
    "/readers",
    operation_id="post_readers",
    status_code=201,
    response_model=schemas.Reader,
)
def create_reader(
    payload: schemas.ReaderCreate, key: Key, uow: Uow, actor: Write
) -> JSONResponse:
    return write(
        uow,
        actor,
        "reader.create",
        lambda: schemas.Reader.model_validate(
            service.create(uow.session, payload, actor.account_id)
        ).model_dump(mode="json"),
        key=key,
        payload=payload.model_dump(mode="json"),
        status=201,
        location="/api/v1/readers",
    )


@router.patch(
    "/readers/{id}", operation_id="patch_readers_id", response_model=schemas.Reader
)
def patch_reader(
    id: uuid.UUID, payload: schemas.ReaderPatch, uow: Uow, actor: Write
) -> JSONResponse:
    return write(
        uow,
        actor,
        "reader.update",
        lambda: schemas.Reader.model_validate(
            service.patch(uow.session, id, payload, actor.account_id)
        ).model_dump(mode="json"),
    )


@router.post(
    "/readers/{id}/cards",
    operation_id="post_readers_id_cards",
    status_code=201,
    response_model=schemas.ReaderCard,
)
def issue_card(id: uuid.UUID, key: Key, uow: Uow, actor: Issue) -> JSONResponse:
    return write(
        uow,
        actor,
        "card.issue",
        lambda: schemas.ReaderCard.model_validate(
            service.issue_card(uow.session, id, actor.account_id)
        ).model_dump(mode="json"),
        key=key,
        payload={"reader_id": str(id)},
        status=201,
        location=f"/api/v1/readers/{id}/cards",
    )


@router.get(
    "/readers/{id}/eligibility",
    operation_id="get_readers_id_eligibility",
    response_model=schemas.Eligibility,
)
def eligibility(id: uuid.UUID, uow: Uow, actor: Eligible) -> dict[str, Any]:
    from lib_management.circulation.service import eligibility as evaluate
    from lib_management.core.errors import NotFound

    if not staff_reader_scope(actor) and actor.account.reader_id != id:
        raise NotFound()
    get(uow.session, models.Reader, id)
    return evaluate(uow.session, id)
