"""Public projections (openapi.json: AccountView, AuthContext)."""

import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AccountView(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    id: uuid.UUID
    reader_id: uuid.UUID | None
    display_name: str = Field(max_length=200)
    status: Literal["ACTIVE", "LOCKED", "DISABLED"]


class AuthContext(BaseModel):
    model_config = ConfigDict(extra="forbid")
    account: AccountView
    permissions: list[str]
