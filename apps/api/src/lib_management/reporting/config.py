"""Local artifact adapter settings; production retention is deployment configured."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ReportingSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")
    artifact_storage_root: Path = Path("/tmp/lib-management-artifacts")
    report_artifact_retention_hours: int = Field(default=24, ge=1, le=8760)
