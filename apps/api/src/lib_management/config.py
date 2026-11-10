"""Environment configuration for the API and worker."""

import re

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_ORIGIN = re.compile(r"https?://[A-Za-z0-9.-]+(:\d{1,5})?")


def _split_origins(value: str) -> list[str]:
    return [o.strip().rstrip("/") for o in value.split(",") if o.strip()]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    db_host: str = "127.0.0.1"
    db_port: int = Field(default=5432, ge=1, le=65535)
    db_user: str = "postgres"
    db_name: str = "lib_management"
    db_password: SecretStr

    # Per process: keep the replica/worker total below Postgres capacity.
    # Zero pool_size and negative overflow mean unlimited in SQLAlchemy.
    db_pool_size: int = Field(default=5, ge=1, le=100)
    db_pool_max_overflow: int = Field(default=5, ge=0, le=100)
    db_pool_timeout_seconds: float = Field(
        default=2.0, gt=0, le=60, allow_inf_nan=False
    )
    db_pool_recycle_seconds: int = Field(default=1800, ge=1, le=86400)

    # OIDC is optional so health-only deployments still start; business routes
    # that need a token fail closed with 503 while it is unset.
    oidc_issuer: str | None = None
    oidc_audience: str = "lib-management-api"
    oidc_jwks_url: str | None = None
    oidc_clock_skew_seconds: int = Field(default=30, ge=0, le=300)

    # Comma-separated browser origins allowed to call the API from another site,
    # e.g. the GitHub Pages build. Empty keeps CORS off (same-origin deployments).
    cors_allow_origins: str = ""

    idempotency_ttl_hours: int = Field(default=24, ge=1, le=24 * 30)
    worker_lease_seconds: int = Field(default=60, ge=5, le=3600)
    worker_max_attempts: int = Field(default=5, ge=1, le=50)

    @field_validator("db_password")
    @classmethod
    def require_password(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value():
            raise ValueError("DB_PASSWORD must be non-empty")
        return value

    @field_validator("cors_allow_origins")
    @classmethod
    def check_origins(cls, value: str) -> str:
        for origin in _split_origins(value):
            if not _ORIGIN.fullmatch(origin):
                raise ValueError(
                    f"CORS_ALLOW_ORIGINS entry {origin!r} must be scheme://host[:port] "
                    "with no path or wildcard"
                )
        return value

    @property
    def cors_origins(self) -> list[str]:
        return _split_origins(self.cors_allow_origins)

    @property
    def jwks_url(self) -> str | None:
        if self.oidc_jwks_url:
            return self.oidc_jwks_url
        if self.oidc_issuer:
            return f"{self.oidc_issuer.rstrip('/')}/protocol/openid-connect/certs"
        return None
