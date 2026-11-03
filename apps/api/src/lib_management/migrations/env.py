"""Alembic environment: online migrations only, URL from Settings."""

from alembic import context
from sqlalchemy import create_engine

from lib_management.config import Settings
from lib_management.migrate import database_url
from lib_management.models import load_all_models

config = context.config
target_metadata = load_all_models().metadata


def run() -> None:
    url = config.attributes.get("database_url") or database_url(Settings())
    engine = create_engine(url, connect_args={"connect_timeout": 5})
    try:
        with engine.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                compare_type=True,
                transaction_per_migration=True,
            )
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


if context.is_offline_mode():
    raise SystemExit("Offline SQL generation is not supported")
run()
