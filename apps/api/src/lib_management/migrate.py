"""Programmatic Alembic access; scripts ship inside the wheel."""

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import URL

from lib_management.config import Settings

SCRIPT_LOCATION = "lib_management:migrations"


def database_url(settings: Settings) -> URL:
    return URL.create(
        "postgresql+psycopg",
        username=settings.db_user,
        password=settings.db_password.get_secret_value(),
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name,
    )


def alembic_config(settings: Settings | None = None) -> Config:
    config = Config()
    config.set_main_option("script_location", SCRIPT_LOCATION)
    if settings is not None:
        # Passed as an attribute, not the ini option: avoids %-interpolation
        # of passwords and never renders the secret into a string.
        config.attributes["database_url"] = database_url(settings)
    return config


def head_revision() -> str | None:
    return ScriptDirectory.from_config(alembic_config()).get_current_head()


def upgrade(settings: Settings, revision: str = "head") -> None:
    command.upgrade(alembic_config(settings), revision)


def downgrade(settings: Settings, revision: str) -> None:
    command.downgrade(alembic_config(settings), revision)
