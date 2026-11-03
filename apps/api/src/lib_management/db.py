"""Database connection and readiness probe."""

import asyncio
from contextlib import suppress

import psycopg
from sqlalchemy import URL, Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from lib_management.config import Settings


def create_engine_from_settings(settings: Settings) -> Engine:
    url = URL.create(
        "postgresql+psycopg",
        username=settings.db_user,
        password=settings.db_password.get_secret_value(),
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name,
    )
    return create_engine(
        url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 2, "options": "-c statement_timeout=2000"},
    )


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Sync sessions for business routes; expire_on_commit off for DTO mapping."""
    return sessionmaker(engine, expire_on_commit=False, autoflush=True)


class DatabaseProbe:
    """Dedicated async connections; deadline includes admission and network reads.

    Close the socket before cancelling the task: psycopg otherwise attempts a
    network cancellation handshake, which can itself stall on a blackhole.
    No pooled connection or synchronous worker is used by health requests.
    """

    def __init__(
        self,
        settings: Settings,
        timeout: float = 2.0,
        expected_revision: str | None = None,
    ) -> None:
        self.settings = settings
        self.timeout = timeout
        self.expected_revision = expected_revision
        self.slots = asyncio.Semaphore(4)

    async def check(self) -> bool:
        connection: psycopg.AsyncConnection[tuple[int]] | None = None

        async def query() -> bool:
            nonlocal connection
            async with self.slots:
                connection = await psycopg.AsyncConnection.connect(
                    host=self.settings.db_host,
                    port=self.settings.db_port,
                    user=self.settings.db_user,
                    password=self.settings.db_password.get_secret_value(),
                    dbname=self.settings.db_name,
                    connect_timeout=2,
                    options="-c statement_timeout=2000",
                    autocommit=True,
                )
                cursor = await connection.execute("SELECT 1")
                row = await cursor.fetchone()
                if row != (1,):
                    return False
                if self.expected_revision is None:
                    return True
                # Schema must be at the migration head shipped with this code.
                revision = await connection.execute(
                    "SELECT version_num FROM alembic_version"
                )
                versions = {str(value[0]) for value in await revision.fetchall()}
                return versions == {self.expected_revision}

        task = asyncio.create_task(query())
        try:
            done, _ = await asyncio.wait({task}, timeout=self.timeout)
            return task.result() if done else False
        except psycopg.Error:
            return False
        finally:
            if connection is not None:
                await connection.close()
            if not task.done():
                task.cancel()
            with suppress(asyncio.CancelledError, psycopg.Error):
                await task
