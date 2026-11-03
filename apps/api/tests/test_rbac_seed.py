import json
from pathlib import Path

from lib_management.identity.rbac_seed import PERMISSIONS, ROLES

OPENAPI = Path(__file__).resolve().parents[3] / "docs" / "design" / "openapi.json"


def contract_permissions() -> set[str]:
    codes: set[str] = set()
    for item in json.loads(OPENAPI.read_text())["paths"].values():
        for operation in item.values():
            if not isinstance(operation, dict):
                continue
            if operation.get("x-permission"):
                codes.add(operation["x-permission"])
            for rule in operation.get("x-authorization", {}).get("rules", []):
                codes.update(rule.get("allPermissions", []))
            for rule in operation.get("x-conditional-permissions", []):
                codes.update(rule.get("allPermissions", []))
    return codes


def test_permission_codes_match_contract():
    assert set(PERMISSIONS) == contract_permissions()
    assert len(PERMISSIONS) == 39


def test_roles_only_grant_known_permissions():
    assert set(ROLES) == {"READER", "LIBRARIAN", "MANAGER", "SYSTEM_ADMIN", "OPS_ADMIN"}
    for _, codes in ROLES.values():
        assert set(codes) <= set(PERMISSIONS)
        assert len(codes) == len(set(codes))


def test_staff_roles_are_cumulative_by_name():
    reader, librarian, manager, admin, ops = (
        set(ROLES[code][1])
        for code in ("READER", "LIBRARIAN", "MANAGER", "SYSTEM_ADMIN", "OPS_ADMIN")
    )
    assert librarian < manager < admin
    assert admin == set(PERMISSIONS)
    assert ops < admin


def test_lower_roles_keep_their_limits():
    librarian = set(ROLES["LIBRARIAN"][1])
    reader = set(ROLES["READER"][1])
    ops = set(ROLES["OPS_ADMIN"][1])
    assert not {"assessment.decide", "charge.waive", "ledger.reverse"} & librarian
    assert not {"role.manage", "account.manage"} & (
        librarian | set(ROLES["MANAGER"][1])
    )
    # Readers only reach /me data; nothing that writes for other readers.
    assert (
        not {"reader.write", "loan.checkout", "payment.collect", "overdue.read"}
        & reader
    )
    # Operations never touches the counter or reader records.
    assert not {"reader.read", "loan.checkout", "payment.collect"} & ops
