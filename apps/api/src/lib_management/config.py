"""Environment configuration for the API."""

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    db_host: str = "127.0.0.1"
    db_port: int = Field(default=5432, ge=1, le=65535)
    db_user: str = "postgres"
    db_name: str = "lib_management"
    db_password: SecretStr

    @field_validator("db_password")
    @classmethod
    def require_password(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value():
            raise ValueError("DB_PASSWORD must be non-empty")
        return value
