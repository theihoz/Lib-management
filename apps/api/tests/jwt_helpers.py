"""Local RSA keys and token factory; no network, no real IdP."""

import time
from typing import Any

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

from lib_management.identity.auth import JwtVerifier

ISSUER = "http://keycloak.test/realms/lib-management"
AUDIENCE = "lib-management-api"
KID = "test-key-1"

PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
OTHER_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


class StaticKeys:
    def __init__(self, keys: dict[str, Any]) -> None:
        self.keys = keys
        self.lookups: list[str] = []

    def get(self, kid: str) -> Any | None:
        self.lookups.append(kid)
        return self.keys.get(kid)


def make_verifier() -> JwtVerifier:
    return JwtVerifier(ISSUER, AUDIENCE, StaticKeys({KID: PRIVATE_KEY.public_key()}))


def make_token(
    subject: str = "user-1",
    *,
    key: Any = PRIVATE_KEY,
    kid: str | None = KID,
    algorithm: str = "RS256",
    **overrides: Any,
) -> str:
    now = int(time.time())
    claims: dict[str, Any] = {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "sub": subject,
        "iat": now,
        "exp": now + 300,
    }
    claims.update(overrides)
    claims = {k: v for k, v in claims.items() if v is not None}
    headers = {"kid": kid} if kid else {}
    return jwt.encode(claims, key, algorithm=algorithm, headers=headers)
