"""Bearer JWT verification and request guards.

Identity comes from Keycloak (signature, iss, aud, exp/nbf); authorization
comes only from the application DB, re-read on every request. Role claims in
the token are ignored.
"""

import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated, Any, Protocol

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session, sessionmaker

from lib_management.core import audit
from lib_management.core.errors import Forbidden, InvalidToken, ServiceUnavailable
from lib_management.core.uow import UnitOfWork, get_uow
from lib_management.identity import repository
from lib_management.identity.models import Account

ALGORITHMS = ["RS256"]
REQUIRED_CLAIMS = ["exp", "iat", "iss", "sub", "aud"]


class KeySource(Protocol):
    def get(self, kid: str) -> Any | None:
        """Returns the verification key for ``kid`` or None."""


class JwksKeySource:
    """Caches JWKS; refreshes once on an unknown kid, at most every 30s."""

    def __init__(self, jwks_url: str, min_refresh_seconds: float = 30.0) -> None:
        self._client = jwt.PyJWKClient(jwks_url, cache_jwk_set=False, timeout=5)
        self._keys: dict[str, Any] = {}
        self._fetched_at = float("-inf")
        self._min_refresh = min_refresh_seconds
        self._lock = threading.Lock()

    def _refresh(self) -> None:
        jwk_set = self._client.get_jwk_set(refresh=True)
        self._keys = {key.key_id: key.key for key in jwk_set.keys if key.key_id}
        self._fetched_at = time.monotonic()

    def get(self, kid: str) -> Any | None:
        with self._lock:
            if kid in self._keys:
                return self._keys[kid]
            if time.monotonic() - self._fetched_at >= self._min_refresh:
                try:
                    self._refresh()
                except jwt.PyJWKClientError as error:
                    raise ServiceUnavailable("Không lấy được khóa xác thực") from error
            return self._keys.get(kid)


@dataclass(frozen=True)
class TokenClaims:
    issuer: str
    subject: str


class JwtVerifier:
    def __init__(
        self, issuer: str, audience: str, keys: KeySource, leeway_seconds: int = 30
    ) -> None:
        self.issuer = issuer
        self.audience = audience
        self.keys = keys
        self.leeway = leeway_seconds

    def verify(self, token: str) -> TokenClaims:
        try:
            header = jwt.get_unverified_header(token)
        except jwt.PyJWTError as error:
            raise InvalidToken() from error
        if header.get("alg") not in ALGORITHMS:
            raise InvalidToken()
        kid = header.get("kid")
        if not isinstance(kid, str) or not kid:
            raise InvalidToken()
        key = self.keys.get(kid)
        if key is None:
            raise InvalidToken()
        try:
            claims = jwt.decode(
                token,
                key,
                algorithms=ALGORITHMS,
                audience=self.audience,
                issuer=self.issuer,
                leeway=self.leeway,
                options={"require": REQUIRED_CLAIMS},
            )
        except jwt.PyJWTError as error:
            raise InvalidToken() from error
        subject = claims.get("sub")
        if not isinstance(subject, str) or not subject:
            raise InvalidToken()
        return TokenClaims(issuer=self.issuer, subject=subject)


@dataclass(frozen=True)
class Principal:
    account: Account
    permissions: frozenset[str]

    @property
    def account_id(self) -> uuid.UUID:
        return self.account.id


_bearer = HTTPBearer(auto_error=False)


def get_verifier(request: Request) -> JwtVerifier:
    verifier: JwtVerifier | None = getattr(request.app.state, "jwt_verifier", None)
    if verifier is None:
        raise ServiceUnavailable("Xác thực chưa được cấu hình")
    return verifier


def current_account(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    verifier: Annotated[JwtVerifier, Depends(get_verifier)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> Account:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise InvalidToken("Thiếu Bearer token")
    claims = verifier.verify(credentials.credentials)
    account = repository.find_account(uow.session, claims.issuer, claims.subject)
    if account is None:
        raise Forbidden("ACCOUNT_NOT_LINKED", "Tài khoản chưa được cấp trong hệ thống")
    if account.status != "ACTIVE":
        raise Forbidden("ACCOUNT_INACTIVE", "Tài khoản đã bị khóa")
    return account


def authenticated(
    account: Annotated[Account, Depends(current_account)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> Principal:
    return Principal(account, repository.permission_codes(uow.session, account.id))


def require_permission(code: str) -> Callable[..., Principal]:
    """Dependency factory: 403 PERMISSION_DENIED + DENIED audit when missing."""

    def guard(
        request: Request, principal: Annotated[Principal, Depends(authenticated)]
    ) -> Principal:
        if code not in principal.permissions:
            _audit_denied(request.app.state.session_factory, principal, code, request)
            raise Forbidden("PERMISSION_DENIED", f"Thiếu quyền {code}")
        return principal

    guard.__name__ = f"require_{code.replace('.', '_')}"
    return guard


def _audit_denied(
    session_factory: sessionmaker[Session],
    principal: Principal,
    code: str,
    request: Request,
) -> None:
    # Separate transaction: the command's own UoW never commits on denial.
    with session_factory() as session, session.begin():
        audit.record(
            session,
            action="permission.denied",
            target_type="route",
            outcome="DENIED",
            actor_id=principal.account_id,
            permission_code=code,
            metadata={"method": request.method, "path": request.url.path},
        )
