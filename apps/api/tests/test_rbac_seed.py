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


def test_separation_of_duties():
    librarian = set(ROLES["LIBRARIAN"][1])
    admin = set(ROLES["SYSTEM_ADMIN"][1])
    assert "assessment.decide" not in librarian
    assert not {"role.manage", "account.manage"} & librarian
    assert not {"payment.collect", "charge.waive", "restore.approve"} & admin
