"""Implemented operations in the design contract must exist at runtime."""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from lib_management.config import Settings
from lib_management.main import create_app

OPENAPI = Path(__file__).resolve().parents[3] / "docs" / "design" / "openapi.json"
METHODS = {"get", "put", "post", "patch", "delete"}


def operations(schema):
    for path, item in schema["paths"].items():
        for method, operation in item.items():
            if method in METHODS:
                yield path, method, operation


def success_codes(operation):
    return {code for code in operation["responses"] if code.startswith("2")}


def test_implemented_operations_match_runtime():
    design = json.loads(OPENAPI.read_text())
    with TestClient(create_app(Settings(db_password="unit-test-fixture"))) as client:
        runtime = client.get("/openapi.json").json()
    runtime_ops = {(p, m): o for p, m, o in operations(runtime)}
    implemented = [
        (p, m, o)
        for p, m, o in operations(design)
        if o.get("x-status") == "implemented"
    ]
    assert ("/api/v1/auth/me", "get") in {(p, m) for p, m, _ in implemented}
    for path, method, operation in implemented:
        actual = runtime_ops.get((path, method))
        assert actual is not None, f"{method.upper()} {path} missing at runtime"
        assert actual["operationId"] == operation["operationId"]
        assert success_codes(actual) == success_codes(operation), path


def test_runtime_has_no_unplanned_business_routes():
    design = json.loads(OPENAPI.read_text())
    with TestClient(create_app(Settings(db_password="unit-test-fixture"))) as client:
        runtime = client.get("/openapi.json").json()
    planned = {(p, m) for p, m, _ in operations(design)}
    extra = {(p, m) for p, m, _ in operations(runtime)} - planned
    assert extra == set()


def test_design_status_matches_runtime_both_ways():
    # x-status must say exactly what is served; run scripts/openapi_status.py to fix.
    design = json.loads(OPENAPI.read_text())
    with TestClient(create_app(Settings(db_password="unit-test-fixture"))) as client:
        runtime = {(p, m) for p, m, _ in operations(client.get("/openapi.json").json())}
    stale = sorted(
        f"{method.upper()} {path} is {operation.get('x-status')}"
        for path, method, operation in operations(design)
        if (operation.get("x-status") == "implemented") != ((path, method) in runtime)
    )
    assert stale == []
