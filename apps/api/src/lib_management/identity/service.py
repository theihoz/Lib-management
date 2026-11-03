"""Identity commands used by the operator CLI (no public API in M0)."""

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from lib_management.core import audit
from lib_management.identity.models import (
    Account,
    AccountRole,
    Permission,
    Role,
    RolePermission,
)
from lib_management.identity.rbac_seed import PERMISSIONS, ROLES


@dataclass
class SeedReport:
    permissions_created: list[str] = field(default_factory=list)
    permissions_updated: list[str] = field(default_factory=list)
    roles_created: list[str] = field(default_factory=list)
    roles_updated: list[str] = field(default_factory=list)
    grants_added: list[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return any(vars(self).values())


def seed_rbac(session: Session) -> SeedReport:
    """Idempotent upsert; only adds grants, never removes explicit ones."""
    report = SeedReport()
    permissions = {p.code: p for p in session.execute(select(Permission)).scalars()}
    for code, description in PERMISSIONS.items():
        existing = permissions.get(code)
        if existing is None:
            permissions[code] = Permission(code=code, description=description)
            session.add(permissions[code])
            report.permissions_created.append(code)
        elif existing.description != description:
            existing.description = description
            report.permissions_updated.append(code)

    roles = {r.code: r for r in session.execute(select(Role)).scalars()}
    for code, (name, _) in ROLES.items():
        role = roles.get(code)
        if role is None:
            roles[code] = Role(code=code, name=name)
            session.add(roles[code])
            report.roles_created.append(code)
        elif role.name != name:
            role.name = name
            report.roles_updated.append(code)
    session.flush()

    granted = {
        (role_id, permission_id)
        for role_id, permission_id in session.execute(
            select(RolePermission.role_id, RolePermission.permission_id)
        )
    }
    for code, (_, codes) in ROLES.items():
        for permission_code in codes:
            pair = (roles[code].id, permissions[permission_code].id)
            if pair not in granted:
                session.add(RolePermission(role_id=pair[0], permission_id=pair[1]))
                report.grants_added.append(f"{code}:{permission_code}")
    session.flush()
    return report


class UnknownRole(ValueError):
    pass


def bootstrap_account(
    session: Session,
    *,
    issuer: str,
    subject: str,
    display_name: str,
    role_codes: list[str],
) -> Account:
    """Operator-only: creates/activates an Account and grants roles."""
    roles = {
        r.code: r
        for r in session.execute(
            select(Role).where(Role.code.in_(role_codes))
        ).scalars()
    }
    missing = sorted(set(role_codes) - roles.keys())
    if missing:
        raise UnknownRole(f"Unknown roles {missing}; run seed-rbac first")

    account = session.execute(
        select(Account).where(Account.issuer == issuer, Account.subject == subject)
    ).scalar_one_or_none()
    created = account is None
    if account is None:
        account = Account(
            issuer=issuer, subject=subject, display_name=display_name, status="ACTIVE"
        )
        session.add(account)
    else:
        account.display_name = display_name
        account.status = "ACTIVE"
    session.flush()

    held = set(
        session.execute(
            select(AccountRole.role_id).where(AccountRole.account_id == account.id)
        ).scalars()
    )
    added = []
    for code in role_codes:
        if roles[code].id not in held:
            session.add(
                AccountRole(
                    account_id=account.id, role_id=roles[code].id, granted_by=account.id
                )
            )
            added.append(code)
    audit.record(
        session,
        action="account.bootstrap",
        target_type="account",
        target_id=account.id,
        outcome="SUCCESS",
        actor_type="SYSTEM",
        metadata={"created": created, "roles_added": added},
    )
    session.flush()
    return account
