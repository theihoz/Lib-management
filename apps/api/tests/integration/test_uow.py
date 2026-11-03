import pytest
from sqlalchemy import func, select

from lib_management.core.uow import UnitOfWork
from lib_management.identity.models import Role


def count(session_factory):
    with session_factory() as session:
        return session.execute(select(func.count()).select_from(Role)).scalar_one()


def test_error_mid_command_rolls_back_everything(session_factory):
    with pytest.raises(RuntimeError), UnitOfWork(session_factory) as uow:
        uow.session.add(Role(code="A", name="a"))
        uow.session.flush()
        uow.session.add(Role(code="B", name="b"))
        raise RuntimeError("boom")
    assert count(session_factory) == 0


def test_missing_commit_discards_writes(session_factory):
    with UnitOfWork(session_factory) as uow:
        uow.session.add(Role(code="A", name="a"))
        uow.session.flush()
    assert count(session_factory) == 0


def test_commit_persists_once(session_factory):
    with UnitOfWork(session_factory) as uow:
        uow.session.add(Role(code="A", name="a"))
        uow.commit()
    assert count(session_factory) == 1
