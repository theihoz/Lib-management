"""ASGI app factory with independent health endpoints and /api/v1."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import APIRouter, FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from lib_management.config import Settings
from lib_management.core.errors import install_error_handlers
from lib_management.core.request_id import RequestIdMiddleware
from lib_management.db import (
    DatabaseProbe,
    create_engine_from_settings,
    create_session_factory,
)
from lib_management.identity.auth import JwksKeySource, JwtVerifier
from lib_management.identity.router import router as identity_router
from lib_management.migrate import head_revision

API_PREFIX = "/api/v1"


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


def create_verifier(settings: Settings) -> JwtVerifier | None:
    if not settings.oidc_issuer or not settings.jwks_url:
        return None
    return JwtVerifier(
        issuer=settings.oidc_issuer,
        audience=settings.oidc_audience,
        keys=JwksKeySource(settings.jwks_url),
        leeway_seconds=settings.oidc_clock_skew_seconds,
    )


def create_app(
    settings: Settings | None = None, *, verifier: JwtVerifier | None = None
) -> FastAPI:
    configuration = settings if settings is not None else Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_engine_from_settings(configuration)
        app.state.engine = engine
        app.state.session_factory = create_session_factory(engine)
        app.state.db_probe = DatabaseProbe(
            configuration, expected_revision=head_revision()
        )
        app.state.jwt_verifier = verifier or create_verifier(configuration)
        app.state.settings = configuration
        try:
            yield
        finally:
            engine.dispose()

    app = FastAPI(title="Lib-management API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(RequestIdMiddleware)
    install_error_handlers(app)

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

    api = APIRouter(prefix=API_PREFIX)
    api.include_router(identity_router)
    app.include_router(api)
    return app
