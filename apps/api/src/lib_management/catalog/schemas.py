"""Typed HTTP schemas following the checked-in API contract."""

import uuid
from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Schema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    @model_validator(mode="after")
    def supplied_fields(self) -> Self:
        if self.__class__.__name__.endswith("Patch"):
            values = self.model_fields_set - {"expected_version"}
            if not values:
                raise ValueError("Provide at least one field to update")
            for name in values:
                if (
                    getattr(self, name) is None
                    and not self.__class__.model_fields[name].json_schema_extra
                ):
                    raise ValueError(f"{name} cannot be null")
        return self


class Publisher(Schema):
    id: uuid.UUID = Field()
    name: str = Field(max_length=200, min_length=1)
    address: str | None = Field(default=None, json_schema_extra={"nullable": True})
    status: str = Field(max_length=16, min_length=1)
    created_at: datetime = Field()


class Author(Schema):
    id: uuid.UUID = Field()
    name: str = Field(max_length=200, min_length=1)
    biography: str | None = Field(default=None, json_schema_extra={"nullable": True})
    status: str = Field(max_length=16, min_length=1)
    created_at: datetime = Field()


class Category(Schema):
    id: uuid.UUID = Field()
    code: str = Field(max_length=32, min_length=1)
    name: str = Field(max_length=120, min_length=1)
    parent_id: uuid.UUID | None = Field(
        default=None, json_schema_extra={"nullable": True}
    )
    is_root: bool = Field()
    created_at: datetime = Field()


class BookEdition(Schema):
    id: uuid.UUID = Field()
    isbn: str | None = Field(
        default=None, max_length=13, json_schema_extra={"nullable": True}
    )
    title: str = Field(max_length=300, min_length=1)
    publication_year: int = Field()
    publisher_id: uuid.UUID | None = Field(
        default=None, json_schema_extra={"nullable": True}
    )
    language: str | None = Field(
        default=None, max_length=32, json_schema_extra={"nullable": True}
    )
    description: str | None = Field(default=None, json_schema_extra={"nullable": True})
    status: str = Field(max_length=16, min_length=1)
    version: int = Field()
    created_at: datetime = Field()


class BookCopy(Schema):
    id: uuid.UUID = Field()
    edition_id: uuid.UUID = Field()
    barcode: str = Field(max_length=64, min_length=1)
    location_id: uuid.UUID | None = Field(
        default=None, json_schema_extra={"nullable": True}
    )
    status: str = Field(max_length=16, min_length=1)
    acquired_at: datetime = Field()
    source_receipt_item_id: uuid.UUID | None = Field(
        default=None, json_schema_extra={"nullable": True}
    )
    version: int = Field()
    created_at: datetime = Field()


class AuthorCreate(Schema):
    name: str = Field(max_length=200, min_length=1)
    biography: str | None = Field(default=None, json_schema_extra={"nullable": True})


class AuthorPatch(Schema):
    name: str | None = Field(default=None, max_length=200, min_length=1)
    biography: str | None = Field(default=None, json_schema_extra={"nullable": True})
    status: Literal["ACTIVE", "INACTIVE"] | None = Field(default=None, min_length=1)


class PublisherCreate(Schema):
    name: str = Field(max_length=200, min_length=1)
    address: str | None = Field(default=None, json_schema_extra={"nullable": True})


class PublisherPatch(Schema):
    name: str | None = Field(default=None, max_length=200, min_length=1)
    address: str | None = Field(default=None, json_schema_extra={"nullable": True})
    status: Literal["ACTIVE", "INACTIVE"] | None = Field(default=None, min_length=1)


class CategoryCreate(Schema):
    code: str = Field(max_length=32, min_length=1)
    name: str = Field(max_length=120, min_length=1)
    parent_id: uuid.UUID | None = Field(
        default=None, alias="parentId", json_schema_extra={"nullable": True}
    )


class CategoryPatch(Schema):
    code: str | None = Field(default=None, max_length=32, min_length=1)
    name: str | None = Field(default=None, max_length=120, min_length=1)
    parent_id: uuid.UUID | None = Field(
        default=None, alias="parentId", json_schema_extra={"nullable": True}
    )
    status: Literal["ACTIVE", "INACTIVE"] | None = Field(default=None, min_length=1)


class BookEditionCreate(Schema):
    title: str = Field(max_length=300, min_length=1)
    publication_year: int = Field(alias="publicationYear")
    isbn: str | None = Field(
        default=None, max_length=13, json_schema_extra={"nullable": True}
    )
    publisher_id: uuid.UUID | None = Field(
        default=None, alias="publisherId", json_schema_extra={"nullable": True}
    )
    language: str | None = Field(
        default=None, max_length=32, json_schema_extra={"nullable": True}
    )
    description: str | None = Field(default=None, json_schema_extra={"nullable": True})
    author_ids: list[uuid.UUID] = Field(default_factory=list, alias="authorIds")
    category_ids: list[uuid.UUID] = Field(default_factory=list, alias="categoryIds")


class BookEditionPatch(Schema):
    title: str | None = Field(default=None, max_length=300, min_length=1)
    publication_year: int | None = Field(default=None, alias="publicationYear")
    isbn: str | None = Field(
        default=None, max_length=13, json_schema_extra={"nullable": True}
    )
    publisher_id: uuid.UUID | None = Field(
        default=None, alias="publisherId", json_schema_extra={"nullable": True}
    )
    language: str | None = Field(
        default=None, max_length=32, json_schema_extra={"nullable": True}
    )
    description: str | None = Field(default=None, json_schema_extra={"nullable": True})
    author_ids: list[uuid.UUID] = Field(default_factory=list, alias="authorIds")
    category_ids: list[uuid.UUID] = Field(default_factory=list, alias="categoryIds")
    expected_version: int = Field(alias="expectedVersion", ge=1)
    status: Literal["ACTIVE", "INACTIVE"] | None = Field(default=None, min_length=1)


class CopiesRequest(Schema):
    barcodes: list[str] = Field(min_length=1)
    location_id: uuid.UUID = Field(alias="locationId")


class LocationCreate(Schema):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=120)
