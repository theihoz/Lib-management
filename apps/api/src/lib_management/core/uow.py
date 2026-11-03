"""Unit of Work: one Session per command; the service commits exactly once."""

from collections.abc import Iterator
from types import TracebackType
from typing import Self

from fastapi import Request
from sqlalchemy.orm import Session, sessionmaker


class UnitOfWork:
    """Rolls back unless ``commit()`` was called; repositories never commit."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._factory = session_factory
        self._session: Session | None = None

    @property
    def session(self) -> Session:
        if self._session is None:
            raise RuntimeError("UnitOfWork used outside its context")
        return self._session

    def __enter__(self) -> Self:
        self._session = self._factory()
        return self

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        session = self.session
        try:
            # Anything not committed is discarded, including on success paths
            # that forgot to commit: partial writes never leak.
            session.rollback()
        finally:
            session.close()
            self._session = None


def get_uow(request: Request) -> Iterator[UnitOfWork]:
    """FastAPI dependency; cached per request so guards and routes share it."""
    with UnitOfWork(request.app.state.session_factory) as uow:
        yield uow
