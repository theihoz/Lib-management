"""Create local Keycloak test users and optionally link them to Accounts.

DEV ONLY. Run inside the Dev Container workspace from apps/api:

    uv run --locked python ../../.devcontainer/keycloak/create_dev_users.py --link
    uv run --locked python ../../.devcontainer/keycloak/create_dev_users.py --link --demo-data
    uv run --locked python ../../.devcontainer/keycloak/create_dev_users.py --token librarian.dev

Passwords come from .devcontainer/.env (KEYCLOAK_ADMIN_PASSWORD,
KEYCLOAK_DEV_USER_PASSWORD); nothing secret is printed or committed.
"""

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

REALM = "lib-management"
USERS = {
    "librarian.dev": ("Thủ thư", "LIBRARIAN"),
    "manager.dev": ("Quản lý", "MANAGER"),
    "admin.dev": ("Admin hệ thống", "SYSTEM_ADMIN"),
    "ops.dev": ("Admin vận hành", "OPS_ADMIN"),
    "reader.dev": ("Độc giả", "READER"),
}


def request(method: str, url: str, token: str | None = None, body: Any = None,
            form: dict[str, str] | None = None) -> Any:
    headers = {}
    data = None
    if form is not None:
        data = urllib.parse.urlencode(form).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=10) as response:
        raw = response.read()
        return json.loads(raw) if raw else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=os.environ.get("KEYCLOAK_URL", "http://keycloak:8080"))
    parser.add_argument("--link", action="store_true",
                        help="also run lib_management.cli bootstrap-admin per user")
    parser.add_argument("--demo-data", action="store_true",
                        help="with --link: run seed-demo and link reader.dev to DG0001")
    parser.add_argument("--token", metavar="USERNAME",
                        help="only print an access token for USERNAME (dev-cli client)")
    args = parser.parse_args()
    if args.token:
        print(request("POST", f"{args.url}/realms/{REALM}/protocol/openid-connect/token",
                      form={"grant_type": "password",
                            "client_id": "lib-management-dev-cli",
                            "username": args.token,
                            "password": os.environ["KEYCLOAK_DEV_USER_PASSWORD"]})
              ["access_token"])
        return 0
    admin_password = os.environ["KEYCLOAK_ADMIN_PASSWORD"]
    user_password = os.environ["KEYCLOAK_DEV_USER_PASSWORD"]
    issuer = os.environ.get("OIDC_ISSUER", f"http://localhost:8080/realms/{REALM}")

    token = request("POST", f"{args.url}/realms/master/protocol/openid-connect/token", form={
        "grant_type": "password", "client_id": "admin-cli",
        "username": "admin", "password": admin_password,
    })["access_token"]
    base = f"{args.url}/admin/realms/{REALM}/users"
    reader_subject = None
    for username, (label, role) in USERS.items():
        found = request("GET", f"{base}?exact=true&username={username}", token)
        if not found:
            request("POST", base, token, {
                "username": username, "enabled": True, "emailVerified": True,
                "email": f"{username}@example.test", "firstName": label,
                "lastName": "Dev", "requiredActions": [],
            })
            found = request("GET", f"{base}?exact=true&username={username}", token)
        user_id = found[0]["id"]
        request("PUT", f"{base}/{user_id}/reset-password", token,
                {"type": "password", "value": user_password, "temporary": False})
        print(f"{username}: subject={user_id} role={role}")
        if role == "READER":
            reader_subject = user_id
        if args.link:
            subprocess.run([
                sys.executable, "-m", "lib_management.cli", "bootstrap-admin",
                "--issuer", issuer, "--subject", user_id,
                "--display-name", f"{label} (dev)", "--role", role,
            ], check=True)
    if args.link and args.demo_data and reader_subject:
        subprocess.run([
            sys.executable, "-m", "lib_management.cli", "seed-demo",
            "--link-issuer", issuer, "--link-subject", reader_subject,
        ], check=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.URLError as error:
        raise SystemExit(f"Keycloak not reachable: {error}") from error
