"""Environment configuration for the API and worker."""

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    db_host: str = "127.0.0.1"
    db_port: int = Field(default=5432, ge=1, le=65535)
    db_user: str = "postgres"
    db_name: str = "lib_management"
    db_password: SecretStr

    # OIDC is optional so health-only deployments still start; business routes
    # that need a token fail closed with 503 while it is unset.
    oidc_issuer: str | None = None
    oidc_audience: str = "lib-management-api"
    oidc_jwks_url: str | None = None
    oidc_clock_skew_seconds: int = Field(default=30, ge=0, le=300)

    idempotency_ttl_hours: int = Field(default=24, ge=1, le=24 * 30)
    worker_lease_seconds: int = Field(default=60, ge=5, le=3600)
    worker_max_attempts: int = Field(default=5, ge=1, le=50)

    @field_validator("db_password")
    @classmethod
    def require_password(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value():
            raise ValueError("DB_PASSWORD must be non-empty")
        return value

    @property
    def jwks_url(self) -> str | None:
        if self.oidc_jwks_url:
            return self.oidc_jwks_url
        if self.oidc_issuer:
            return f"{self.oidc_issuer.rstrip('/')}/protocol/openid-connect/certs"
        return None
