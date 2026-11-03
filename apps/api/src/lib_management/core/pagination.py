"""Opaque keyset cursor: default 20, max 100, response {data, nextCursor}."""

import base64
import binascii
import json
import uuid
from typing import Annotated, Any

from fastapi import Query
from pydantic import BaseModel, ConfigDict

from lib_management.core.errors import ValidationFailed

DEFAULT_LIMIT = 20
MAX_LIMIT = 100


class Page[T](BaseModel):
    model_config = ConfigDict(extra="forbid")
    data: list[T]
    nextCursor: str | None


class Cursor(BaseModel):
    """Sort-key values plus the tie-breaking id of the last returned row."""

    model_config = ConfigDict(extra="forbid")
    k: list[str]
    id: uuid.UUID


class PageParams(BaseModel):
    cursor: Cursor | None
    limit: int


def encode_cursor(keys: list[str], last_id: uuid.UUID) -> str:
    raw = json.dumps({"k": keys, "id": str(last_id)}, separators=(",", ":"))
    return base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")


def decode_cursor(value: str) -> Cursor:
    try:
        padded = value + "=" * (-len(value) % 4)
        payload: Any = json.loads(base64.urlsafe_b64decode(padded.encode()))
        return Cursor.model_validate(payload)
    except (binascii.Error, ValueError, UnicodeDecodeError) as error:
        raise ValidationFailed(
            "Cursor không hợp lệ",
            [{"loc": ["query", "cursor"], "msg": "invalid cursor", "type": "cursor"}],
        ) from error


def page_params(
    cursor: Annotated[str | None, Query(max_length=1000)] = None,
    limit: Annotated[int, Query(ge=1, le=MAX_LIMIT)] = DEFAULT_LIMIT,
) -> PageParams:
    """FastAPI dependency for list endpoints."""
    return PageParams(
        cursor=decode_cursor(cursor) if cursor is not None else None, limit=limit
    )


def build_page[T](rows: list[T], limit: int, key: Any) -> Page[T]:
    """``rows`` must be fetched with ``limit + 1``; ``key(row)`` → (keys, id)."""
    has_more = len(rows) > limit
    items = rows[:limit]
    next_cursor = None
    if has_more and items:
        keys, last_id = key(items[-1])
        next_cursor = encode_cursor(keys, last_id)
    return Page[T](data=items, nextCursor=next_cursor)


__all__ = [
    "DEFAULT_LIMIT",
    "MAX_LIMIT",
    "Cursor",
    "Page",
    "PageParams",
    "build_page",
    "decode_cursor",
    "encode_cursor",
    "page_params",
]
