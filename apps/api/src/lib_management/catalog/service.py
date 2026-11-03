"""Catalog commands share the caller's transaction and never commit."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, func, or_, select, text
from sqlalchemy.orm import Session

from lib_management.catalog import models, schemas
from lib_management.core import audit
from lib_management.core.errors import Conflict, NotFound, ValidationFailed
from lib_management.core.pagination import PageParams, encode_cursor
from lib_management.models import Base


def get[T: Base](
    session: Session, model: type[T], identity: uuid.UUID, *, lock: bool = False
) -> T:
    statement = select(model).where(model.id == identity)  # type: ignore[attr-defined]
    if lock:
        statement = statement.with_for_update().execution_options(
            populate_existing=True
        )
    row = session.scalar(statement)
    if row is None:
        raise NotFound()
    return row


def page(
    session: Session,
    model: Any,
    params: PageParams,
    query: str | None = None,
    **filters: Any,
) -> dict[str, Any]:
    statement = select(model).filter_by(**filters)
    if query:
        columns = [
            getattr(model, key)
            for key in ("name", "title", "isbn", "barcode", "full_name", "reader_code")
            if hasattr(model, key)
        ]
        statement = statement.where(
            or_(*(column.ilike(f"%{query}%", escape="\\") for column in columns))
        )
    if params.cursor is not None:
        if params.cursor.k:
            raise ValidationFailed("Cursor không hợp lệ cho danh sách này")
        statement = statement.where(model.id > params.cursor.id)
    rows = list(session.scalars(statement.order_by(model.id).limit(params.limit + 1)))
    return {
        "data": rows[: params.limit],
        "nextCursor": encode_cursor([], rows[params.limit - 1].id)
        if len(rows) > params.limit
        else None,
    }


def changed(
    session: Session,
    row: Any,
    actor_id: uuid.UUID,
    action: str,
    permission: str = "catalog.write",
) -> None:
    session.flush()
    audit.record(
        session,
        action=action,
        target_type=row.__tablename__,
        target_id=row.id,
        actor_id=actor_id,
        permission_code=permission,
        outcome="SUCCESS",
    )


def reference(session: Session, model: Any, identity: uuid.UUID | None) -> None:
    if identity is not None:
        row = get(session, model, identity, lock=True)
        if getattr(row, "status", "ACTIVE") != "ACTIVE":
            raise ValidationFailed("Danh mục tham chiếu không hoạt động")


def normalize_isbn(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.replace("-", "").replace(" ", "").upper()
    if len(value) == 10:
        if (
            not value[:9].isdigit()
            or value[-1] not in "0123456789X"
            or sum((10 - i) * (10 if c == "X" else int(c)) for i, c in enumerate(value))
            % 11
        ):
            raise ValidationFailed("ISBN không hợp lệ")
        prefix = "978" + value[:9]
        value = prefix + str(
            (-sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(prefix))) % 10
        )
    if (
        len(value) != 13
        or not value.isdigit()
        or sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(value)) % 10
    ):
        raise ValidationFailed("ISBN không hợp lệ")
    return value


def validate_year(session: Session, year: int) -> None:
    from zoneinfo import ZoneInfo

    from lib_management.circulation.service import active_policy

    policy = active_policy(session)
    current = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).year
    if not current - policy.rules["publicationYearWindow"] <= year <= current:
        raise ValidationFailed("Năm xuất bản ngoài khoảng cho phép")


def set_links(session: Session, row: models.BookEdition, data: dict[str, Any]) -> None:
    for field, link, foreign, reference_model in [
        ("author_ids", models.BookAuthor, "author_id", models.Author),
        ("category_ids", models.BookCategory, "category_id", models.Category),
    ]:
        if field not in data:
            continue
        identities = data.pop(field)
        if len(identities) != len(set(identities)):
            raise ValidationFailed("Định danh tham chiếu bị trùng")
        for identity in sorted(identities):
            reference(session, reference_model, identity)
        session.execute(delete(link).where(getattr(link, "edition_id") == row.id))
        for index, identity in enumerate(identities, 1):
            values = {"edition_id": row.id, foreign: identity}
            if field == "author_ids":
                values["ordinal"] = index
            session.add(link(**values))


def edition_create(
    session: Session, payload: schemas.BookEditionCreate, actor_id: uuid.UUID
) -> models.BookEdition:
    data = payload.model_dump()
    validate_year(session, data["publication_year"])
    reference(session, models.Publisher, data.get("publisher_id"))
    data["isbn"] = normalize_isbn(data.get("isbn"))
    links = {key: data.pop(key) for key in ("author_ids", "category_ids")}
    row = models.BookEdition(**data, status="ACTIVE")
    session.add(row)
    session.flush()
    set_links(session, row, links)
    changed(session, row, actor_id, "catalog.edition.create")
    return row


def edition_patch(
    session: Session,
    identity: uuid.UUID,
    payload: schemas.BookEditionPatch,
    actor_id: uuid.UUID,
) -> models.BookEdition:
    row = get(session, models.BookEdition, identity, lock=True)
    data = payload.model_dump(exclude_unset=True)
    if data.pop("expected_version") != row.version:
        raise Conflict("Phiên bản đã thay đổi", code="VERSION_CONFLICT")
    if "publication_year" in data:
        validate_year(session, data["publication_year"])
    if "isbn" in data:
        data["isbn"] = normalize_isbn(data["isbn"])
    if "publisher_id" in data:
        reference(session, models.Publisher, data["publisher_id"])
    set_links(session, row, data)
    for key, value in data.items():
        setattr(row, key, value)
    row.version += 1
    changed(session, row, actor_id, "catalog.edition.update")
    return row


def category_parent(
    session: Session, identity: uuid.UUID | None, parent_id: uuid.UUID | None
) -> None:
    # Serialize tree mutations, including two concurrent reparentings.
    session.execute(
        text(
            "SELECT pg_advisory_xact_lock(hashtextextended('catalog.category.tree',0))"
        )
    )
    visited = {identity}
    while parent_id is not None:
        if parent_id in visited:
            raise ValidationFailed("Cây thể loại không được có chu trình")
        visited.add(parent_id)
        parent_id = get(session, models.Category, parent_id).parent_id


def reference_create(
    session: Session, model: Any, payload: Any, actor_id: uuid.UUID
) -> Any:
    data = payload.model_dump()
    if model is models.Category:
        category_parent(session, None, data.get("parent_id"))
    else:
        data["status"] = "ACTIVE"
    row = model(**data)
    session.add(row)
    changed(session, row, actor_id, f"catalog.{row.__tablename__}.create")
    return row


def reference_patch(
    session: Session, model: Any, identity: uuid.UUID, payload: Any, actor_id: uuid.UUID
) -> Any:
    # Tree lock precedes any category row lock to avoid lock inversion.
    data = payload.model_dump(exclude_unset=True)
    if model is models.Category:
        category_parent(session, identity, data.get("parent_id"))
    row = get(session, model, identity, lock=True)
    if model is models.Category:
        if row.is_root and data:
            raise Conflict("Thể loại gốc được bảo vệ", code="ROOT_CATEGORY_PROTECTED")
        if "status" in data:
            raise ValidationFailed(
                "Thể loại không có thuộc tính trạng thái; hãy sửa cây thể loại"
            )
    if data.get("status") == "INACTIVE":
        link_model: Any = (
            models.BookAuthor if model is models.Author else models.BookEdition
        )
        foreign = (
            models.BookAuthor.author_id
            if model is models.Author
            else models.BookEdition.publisher_id
        )
        if session.scalar(
            select(func.count()).select_from(link_model).where(foreign == identity)
        ):
            raise Conflict(
                "Danh mục đang được ấn bản tham chiếu", code="RESOURCE_IN_USE"
            )
    for key, value in data.items():
        setattr(row, key, value)
    changed(session, row, actor_id, f"catalog.{row.__tablename__}.update")
    return row


def add_copies(
    session: Session,
    identity: uuid.UUID,
    payload: schemas.CopiesRequest,
    actor_id: uuid.UUID,
) -> list[models.BookCopy]:
    row = get(session, models.BookEdition, identity, lock=True)
    if row.status != "ACTIVE":
        raise ValidationFailed("Ấn bản không hoạt động")
    reference(session, models.Location, payload.location_id)
    if len(payload.barcodes) != len(set(payload.barcodes)) or any(
        not code.strip() or len(code) > 64 for code in payload.barcodes
    ):
        raise ValidationFailed("Mã vạch trống, trùng hoặc quá dài")
    now = datetime.now(UTC)
    copies = [
        models.BookCopy(
            edition_id=identity,
            barcode=barcode,
            location_id=payload.location_id,
            status="AVAILABLE",
            acquired_at=now,
        )
        for barcode in payload.barcodes
    ]
    session.add_all(copies)
    session.flush()
    for copy in copies:
        changed(session, copy, actor_id, "catalog.copy.create")
    return copies


def public_editions(
    session: Session, editions: list[models.BookEdition]
) -> list[dict[str, Any]]:
    ids = [row.id for row in editions]
    if not ids:
        return []
    authors: dict[uuid.UUID, list[dict[str, Any]]] = {identity: [] for identity in ids}
    for edition_id, author in session.execute(
        select(models.BookAuthor.edition_id, models.Author)
        .join(models.Author, models.Author.id == models.BookAuthor.author_id)
        .where(models.BookAuthor.edition_id.in_(ids))
        .order_by(models.BookAuthor.ordinal)
    ):
        authors[edition_id].append({"id": author.id, "name": author.name})
    categories: dict[uuid.UUID, list[dict[str, Any]]] = {
        identity: [] for identity in ids
    }
    for edition_id, category in session.execute(
        select(models.BookCategory.edition_id, models.Category)
        .join(models.Category, models.Category.id == models.BookCategory.category_id)
        .where(models.BookCategory.edition_id.in_(ids))
        .order_by(models.Category.code)
    ):
        categories[edition_id].append(
            schemas.Category.model_validate(category).model_dump()
        )
    available = dict(
        session.execute(
            select(models.BookCopy.edition_id, func.count())
            .where(
                models.BookCopy.edition_id.in_(ids),
                models.BookCopy.status == "AVAILABLE",
            )
            .group_by(models.BookCopy.edition_id)
        ).all()
    )
    from lib_management.circulation.models import Reservation

    holds = dict(
        session.execute(
            select(Reservation.edition_id, func.count())
            .where(
                Reservation.edition_id.in_(ids),
                Reservation.status.in_(["QUEUED", "READY"]),
            )
            .group_by(Reservation.edition_id)
        ).all()
    )
    now = datetime.now(UTC)
    return [
        {
            **{
                key: getattr(row, key)
                for key in (
                    "id",
                    "title",
                    "isbn",
                    "publication_year",
                    "language",
                    "description",
                )
            },
            "authors": authors[row.id],
            "categories": categories[row.id],
            "cover": None,
            "availability": {
                "availableCount": available.get(row.id, 0),
                "holdQueueCount": holds.get(row.id, 0),
                "asOf": now,
            },
        }
        for row in editions
    ]
