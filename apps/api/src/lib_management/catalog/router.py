"""Catalog HTTP endpoints backed by transactional SQLAlchemy services."""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, Query
from fastapi.responses import JSONResponse

from lib_management.catalog import models, schemas, service
from lib_management.catalog.http import write
from lib_management.core.pagination import Page, PageParams, page_params
from lib_management.core.uow import UnitOfWork, get_uow
from lib_management.identity.auth import Principal, require_permission

router = APIRouter(tags=["catalog"])
Uow = Annotated[UnitOfWork, Depends(get_uow)]
Read = Annotated[Principal, Depends(require_permission("catalog.read"))]
Write = Annotated[Principal, Depends(require_permission("catalog.write"))]
Paging = Annotated[PageParams, Depends(page_params)]
Key = Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)]


@router.get("/authors", operation_id="get_authors", response_model=Page[schemas.Author])
def list_authors(
    uow: Uow,
    actor: Read,
    paging: Paging,
    query: Annotated[str | None, Query(max_length=300)] = None,
) -> dict[str, Any]:
    result = service.page(uow.session, models.Author, paging, query)
    return result


@router.get(
    "/authors/{id}", operation_id="get_authors_id", response_model=schemas.Author
)
def get_authors(id: uuid.UUID, uow: Uow, actor: Read) -> Any:
    row = service.get(uow.session, models.Author, id)
    return row


@router.post(
    "/authors",
    operation_id="post_authors",
    status_code=201,
    response_model=schemas.Author,
)
def create_authors(
    payload: schemas.AuthorCreate, key: Key, uow: Uow, actor: Write
) -> JSONResponse:
    return write(
        uow,
        actor,
        "authors.create",
        lambda: schemas.Author.model_validate(
            service.reference_create(
                uow.session, models.Author, payload, actor.account_id
            )
        ).model_dump(mode="json"),
        key=key,
        payload=payload.model_dump(mode="json"),
        status=201,
        location="/api/v1/authors",
    )


@router.patch(
    "/authors/{id}", operation_id="patch_authors_id", response_model=schemas.Author
)
def patch_authors(
    id: uuid.UUID, payload: schemas.AuthorPatch, uow: Uow, actor: Write
) -> JSONResponse:
    return write(
        uow,
        actor,
        "authors.update",
        lambda: schemas.Author.model_validate(
            service.reference_patch(
                uow.session, models.Author, id, payload, actor.account_id
            )
        ).model_dump(mode="json"),
    )


@router.get(
    "/publishers", operation_id="get_publishers", response_model=Page[schemas.Publisher]
)
def list_publishers(
    uow: Uow,
    actor: Read,
    paging: Paging,
    query: Annotated[str | None, Query(max_length=300)] = None,
) -> dict[str, Any]:
    result = service.page(uow.session, models.Publisher, paging, query)
    return result


@router.get(
    "/publishers/{id}",
    operation_id="get_publishers_id",
    response_model=schemas.Publisher,
)
def get_publishers(id: uuid.UUID, uow: Uow, actor: Read) -> Any:
    row = service.get(uow.session, models.Publisher, id)
    return row


@router.post(
    "/publishers",
    operation_id="post_publishers",
    status_code=201,
    response_model=schemas.Publisher,
)
def create_publishers(
    payload: schemas.PublisherCreate, key: Key, uow: Uow, actor: Write
) -> JSONResponse:
    return write(
        uow,
        actor,
        "publishers.create",
        lambda: schemas.Publisher.model_validate(
            service.reference_create(
                uow.session, models.Publisher, payload, actor.account_id
            )
        ).model_dump(mode="json"),
        key=key,
        payload=payload.model_dump(mode="json"),
        status=201,
        location="/api/v1/publishers",
    )


@router.patch(
    "/publishers/{id}",
    operation_id="patch_publishers_id",
    response_model=schemas.Publisher,
)
def patch_publishers(
    id: uuid.UUID, payload: schemas.PublisherPatch, uow: Uow, actor: Write
) -> JSONResponse:
    return write(
        uow,
        actor,
        "publishers.update",
        lambda: schemas.Publisher.model_validate(
            service.reference_patch(
                uow.session, models.Publisher, id, payload, actor.account_id
            )
        ).model_dump(mode="json"),
    )


@router.get(
    "/categories", operation_id="get_categories", response_model=Page[schemas.Category]
)
def list_categories(
    uow: Uow,
    actor: Read,
    paging: Paging,
    query: Annotated[str | None, Query(max_length=300)] = None,
) -> dict[str, Any]:
    result = service.page(uow.session, models.Category, paging, query)
    return result


@router.get(
    "/categories/{id}",
    operation_id="get_categories_id",
    response_model=schemas.Category,
)
def get_categories(id: uuid.UUID, uow: Uow, actor: Read) -> Any:
    row = service.get(uow.session, models.Category, id)
    return row


@router.post(
    "/categories",
    operation_id="post_categories",
    status_code=201,
    response_model=schemas.Category,
)
def create_categories(
    payload: schemas.CategoryCreate, key: Key, uow: Uow, actor: Write
) -> JSONResponse:
    return write(
        uow,
        actor,
        "categories.create",
        lambda: schemas.Category.model_validate(
            service.reference_create(
                uow.session, models.Category, payload, actor.account_id
            )
        ).model_dump(mode="json"),
        key=key,
        payload=payload.model_dump(mode="json"),
        status=201,
        location="/api/v1/categories",
    )


@router.patch(
    "/categories/{id}",
    operation_id="patch_categories_id",
    response_model=schemas.Category,
)
def patch_categories(
    id: uuid.UUID, payload: schemas.CategoryPatch, uow: Uow, actor: Write
) -> JSONResponse:
    return write(
        uow,
        actor,
        "categories.update",
        lambda: schemas.Category.model_validate(
            service.reference_patch(
                uow.session, models.Category, id, payload, actor.account_id
            )
        ).model_dump(mode="json"),
    )


@router.get("/book-editions", operation_id="get_book_editions", response_model=None)
def list_book_editions(
    uow: Uow,
    paging: Paging,
    query: Annotated[str | None, Query(max_length=300)] = None,
) -> dict[str, Any]:
    result = service.page(
        uow.session, models.BookEdition, paging, query, status="ACTIVE"
    )
    result["data"] = service.public_editions(uow.session, result["data"])
    return result


@router.get(
    "/book-editions/{id}", operation_id="get_book_editions_id", response_model=None
)
def get_book_editions(id: uuid.UUID, uow: Uow) -> Any:
    row = service.get(uow.session, models.BookEdition, id)
    if row.status != "ACTIVE":
        from lib_management.core.errors import NotFound

        raise NotFound()
    return service.public_editions(uow.session, [row])[0]


@router.post(
    "/book-editions",
    operation_id="post_book_editions",
    status_code=201,
    response_model=schemas.BookEdition,
)
def create_book_editions(
    payload: schemas.BookEditionCreate, key: Key, uow: Uow, actor: Write
) -> JSONResponse:
    return write(
        uow,
        actor,
        "book_editions.create",
        lambda: schemas.BookEdition.model_validate(
            service.edition_create(uow.session, payload, actor.account_id)
        ).model_dump(mode="json"),
        key=key,
        payload=payload.model_dump(mode="json"),
        status=201,
        location="/api/v1/book-editions",
    )


@router.patch(
    "/book-editions/{id}",
    operation_id="patch_book_editions_id",
    response_model=schemas.BookEdition,
)
def patch_book_editions(
    id: uuid.UUID, payload: schemas.BookEditionPatch, uow: Uow, actor: Write
) -> JSONResponse:
    return write(
        uow,
        actor,
        "book_editions.update",
        lambda: schemas.BookEdition.model_validate(
            service.edition_patch(uow.session, id, payload, actor.account_id)
        ).model_dump(mode="json"),
    )


@router.get(
    "/book-editions/{id}/copies",
    operation_id="get_book_editions_id_copies",
    response_model=Page[schemas.BookCopy],
)
def list_copies(
    id: uuid.UUID,
    uow: Uow,
    actor: Read,
    paging: Paging,
    query: Annotated[str | None, Query(max_length=300)] = None,
) -> dict[str, Any]:
    service.get(uow.session, models.BookEdition, id)
    return service.page(uow.session, models.BookCopy, paging, query, edition_id=id)


@router.post(
    "/book-editions/{id}/copies",
    operation_id="post_book_editions_id_copies",
    status_code=201,
    response_model=schemas.BookCopy,
)
def create_copies(
    id: uuid.UUID, payload: schemas.CopiesRequest, key: Key, uow: Uow, actor: Write
) -> JSONResponse:
    return write(
        uow,
        actor,
        "book_copies.create",
        lambda: schemas.BookCopy.model_validate(
            service.add_copies(uow.session, id, payload, actor.account_id)[0]
        ).model_dump(mode="json"),
        key=key,
        payload={"edition_id": str(id), **payload.model_dump(mode="json")},
        status=201,
        location=f"/api/v1/book-editions/{id}/copies",
    )


@router.get("/locations", operation_id="get_locations")
def list_locations(
    uow: Uow,
    actor: Read,
    paging: Paging,
    query: Annotated[str | None, Query(max_length=300)] = None,
) -> dict[str, Any]:
    from lib_management.circulation.service import view

    result = service.page(uow.session, models.Location, paging, query)
    result["data"] = [view(row) for row in result["data"]]
    return result


@router.post("/locations", operation_id="post_locations", status_code=201)
def create_location(
    payload: schemas.LocationCreate, key: Key, uow: Uow, actor: Write
) -> JSONResponse:
    from lib_management.circulation.service import view

    return write(
        uow,
        actor,
        "catalog.location.create",
        lambda: view(
            service.reference_create(
                uow.session, models.Location, payload, actor.account_id
            )
        ),
        key=key,
        payload=payload.model_dump(mode="json"),
        status=201,
        location="/api/v1/locations",
    )


@router.get("/copies/lookup", operation_id="get_copies_lookup")
def lookup_copy(
    uow: Uow, actor: Read, barcode: Annotated[str, Query(min_length=1, max_length=64)]
) -> dict[str, Any]:
    from sqlalchemy import select
    from lib_management.circulation.models import Loan, LoanItem
    from lib_management.circulation.service import view
    from lib_management.core.errors import NotFound

    copy = uow.session.scalar(
        select(models.BookCopy).where(models.BookCopy.barcode == barcode)
    )
    if copy is None:
        raise NotFound()
    edition = service.get(uow.session, models.BookEdition, copy.edition_id)
    item = uow.session.scalar(
        select(LoanItem).where(
            LoanItem.copy_id == copy.id, LoanItem.closed_at.is_(None)
        )
    )
    loan = uow.session.get(Loan, item.loan_id) if item else None
    return {
        "copy": view(copy),
        "edition": view(edition),
        "loanItem": view(item) if item else None,
        "loan": view(loan) if loan else None,
    }
