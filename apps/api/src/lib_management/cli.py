"""Operator commands: ``python -m lib_management.cli <command>``.

None of these run automatically at startup.
"""

import argparse
import sys

from lib_management import migrate
from lib_management.config import Settings
from lib_management.db import create_engine_from_settings, create_session_factory
from lib_management.identity import service


def _session_factory(settings: Settings):  # type: ignore[no-untyped-def]
    return create_session_factory(create_engine_from_settings(settings))


def cmd_migrate(args: argparse.Namespace) -> int:
    migrate.upgrade(Settings(), args.revision)
    print(f"Upgraded to {args.revision}")
    return 0


def cmd_downgrade(args: argparse.Namespace) -> int:
    migrate.downgrade(Settings(), args.revision)
    print(f"Downgraded to {args.revision}")
    return 0


def cmd_seed_rbac(args: argparse.Namespace) -> int:
    factory = _session_factory(Settings())
    with factory() as session, session.begin():
        report = service.seed_rbac(session)
    if not report.changed:
        print("RBAC already up to date")
    for label, items in vars(report).items():
        if items:
            print(f"{label}: {len(items)}")
            for item in items:
                print(f"  + {item}")
    return 0


def cmd_bootstrap_admin(args: argparse.Namespace) -> int:
    factory = _session_factory(Settings())
    try:
        with factory() as session, session.begin():
            account = service.bootstrap_account(
                session,
                issuer=args.issuer,
                subject=args.subject,
                display_name=args.display_name,
                role_codes=args.role,
            )
            account_id = account.id
    except service.UnknownRole as error:
        print(error, file=sys.stderr)
        return 2
    print(f"Account {account_id} ACTIVE with roles {sorted(args.role)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m lib_management.cli")
    commands = parser.add_subparsers(dest="command", required=True)

    up = commands.add_parser("migrate", help="alembic upgrade (default head)")
    up.add_argument("--revision", default="head")
    up.set_defaults(func=cmd_migrate)

    down = commands.add_parser("downgrade", help="alembic downgrade to REVISION")
    down.add_argument("revision")
    down.set_defaults(func=cmd_downgrade)

    seed = commands.add_parser("seed-rbac", help="upsert permissions and roles")
    seed.set_defaults(func=cmd_seed_rbac)

    boot = commands.add_parser("bootstrap-admin", help="link an IdP subject")
    boot.add_argument("--issuer", required=True)
    boot.add_argument("--subject", required=True)
    boot.add_argument("--display-name", required=True)
    boot.add_argument("--role", action="append", required=True)
    boot.set_defaults(func=cmd_bootstrap_admin)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result: int = args.func(args)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
