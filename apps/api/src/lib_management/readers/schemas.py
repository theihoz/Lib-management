"""Typed HTTP schemas following the checked-in API contract."""

import uuid
from datetime import date, datetime
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


# BM02 / Lab 3 ReaderCard.card_type.
ReaderType = Literal["X", "Y", "Z"]


class Reader(Schema):
    id: uuid.UUID = Field()
    reader_code: str = Field(max_length=32, min_length=1)
    full_name: str = Field(max_length=200, min_length=1)
    birth_date: date = Field()
    reader_type: str = Field(max_length=8, min_length=1)
    email: str | None = Field(
        default=None, max_length=254, json_schema_extra={"nullable": True}
    )
    phone: str | None = Field(
        default=None, max_length=32, json_schema_extra={"nullable": True}
    )
    address: str | None = Field(default=None, json_schema_extra={"nullable": True})
    status: str = Field(max_length=16, min_length=1)
    version: int = Field()
    created_at: datetime = Field()


class ReaderCard(Schema):
    id: uuid.UUID = Field()
    reader_id: uuid.UUID = Field()
    card_no: str = Field(max_length=64, min_length=1)
    issued_at: datetime = Field()
    expires_at: datetime = Field()
    status: str = Field(max_length=16, min_length=1)
    issued_by: uuid.UUID = Field()
    policy_version_id: uuid.UUID = Field()
    version: int = Field()
    created_at: datetime = Field()


class ReaderCreate(Schema):
    reader_code: str = Field(alias="readerCode", max_length=32, min_length=1)
    full_name: str = Field(alias="fullName", max_length=200, min_length=1)
    birth_date: date = Field(alias="birthDate")
    reader_type: ReaderType = Field(alias="readerType")
    email: str | None = Field(
        default=None, max_length=254, json_schema_extra={"nullable": True}
    )
    phone: str | None = Field(
        default=None, max_length=32, json_schema_extra={"nullable": True}
    )
    address: str | None = Field(default=None, json_schema_extra={"nullable": True})


class ReaderPatch(Schema):
    reader_code: str | None = Field(
        default=None, alias="readerCode", max_length=32, min_length=1
    )
    full_name: str | None = Field(
        default=None, alias="fullName", max_length=200, min_length=1
    )
    birth_date: date | None = Field(default=None, alias="birthDate")
    reader_type: ReaderType | None = Field(default=None, alias="readerType")
    email: str | None = Field(
        default=None, max_length=254, json_schema_extra={"nullable": True}
    )
    phone: str | None = Field(
        default=None, max_length=32, json_schema_extra={"nullable": True}
    )
    address: str | None = Field(default=None, json_schema_extra={"nullable": True})
    expected_version: int = Field(alias="expectedVersion", ge=1)
    status: Literal["ACTIVE", "INACTIVE"] | None = Field(default=None, min_length=1)


class Eligibility(Schema):
    allowed: bool = Field()
    reasons: list[str] = Field()
    policy_version_id: uuid.UUID = Field(alias="policyVersionId")
    evaluated_at: datetime = Field(alias="evaluatedAt")
