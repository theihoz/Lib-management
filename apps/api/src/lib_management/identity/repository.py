"""Identity queries. Repositories never commit."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from lib_management.identity.models import (
    Account,
    AccountRole,
    Permission,
    RolePermission,
)


def find_account(session: Session, issuer: str, subject: str) -> Account | None:
    return session.execute(
        select(Account).where(Account.issuer == issuer, Account.subject == subject)
    ).scalar_one_or_none()


def permission_codes(session: Session, account_id: uuid.UUID) -> frozenset[str]:
    rows = session.execute(
        select(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(AccountRole, AccountRole.role_id == RolePermission.role_id)
        .where(AccountRole.account_id == account_id)
        .distinct()
    ).scalars()
    return frozenset(rows)
