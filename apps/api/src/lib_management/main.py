"""ASGI app factory with independent health endpoints."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from lib_management.config import Settings
from lib_management.db import DatabaseProbe, create_engine_from_settings


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

    @app.get("/health/live")
    async def live() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready")
    async def ready() -> JSONResponse:
        if await app.state.db_probe.check():
            return JSONResponse({"status": "ready"})
        return JSONResponse({"status": "not_ready"}, status_code=503)

    return app
