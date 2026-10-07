"""ASGI app factory with independent health endpoints."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from lib_management.config import Settings
from lib_management.db import DatabaseProbe, create_engine_from_settings


class Health(BaseModel):
    """Public probe payload shared with the design contract."""

    model_config = ConfigDict(extra="forbid")
    status: Literal["ok", "ready", "not_ready"]


class LiveHealth(Health):
    status: Literal["ok"]


class ReadyHealth(Health):
    status: Literal["ready"]


class NotReadyHealth(Health):
    status: Literal["not_ready"]


def create_app(settings: Settings | None = None) -> FastAPI:
    configuration = settings if settings is not None else Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_engine_from_settings(configuration)
        app.state.engine = engine
        app.state.db_probe = DatabaseProbe(configuration)
        try:
            yield
        finally:
            engine.dispose()

    app = FastAPI(lifespan=lifespan)

    @app.get("/health/live", operation_id="health_live", response_model=LiveHealth)
    async def live() -> LiveHealth:
        return LiveHealth(status="ok")

    @app.get(
        "/health/ready",
        operation_id="health_ready",
        response_model=ReadyHealth,
        responses={503: {"model": NotReadyHealth, "description": "DB unavailable"}},
    )
    async def ready() -> ReadyHealth | JSONResponse:
        if await app.state.db_probe.check():
            return ReadyHealth(status="ready")
        return JSONResponse(
            NotReadyHealth(status="not_ready").model_dump(), status_code=503
        )

    return app
