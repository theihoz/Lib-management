import time

import jwt
import pytest

from lib_management.core.errors import InvalidToken
from tests.jwt_helpers import (
    AUDIENCE,
    ISSUER,
    OTHER_KEY,
    make_token,
    make_verifier,
)


def test_valid_token_returns_claims():
    claims = make_verifier().verify(make_token("abc"))
    assert (claims.issuer, claims.subject) == (ISSUER, "abc")


def test_audience_list_containing_api_is_accepted():
    token = make_token(aud=["account", AUDIENCE])
    assert make_verifier().verify(token).subject == "user-1"


@pytest.mark.parametrize(
    "token",
    [
        pytest.param(make_token(iss="http://evil.test/realms/x"), id="wrong-iss"),
        pytest.param(make_token(aud="account"), id="wrong-aud"),
        pytest.param(make_token(exp=int(time.time()) - 31), id="expired"),
        pytest.param(make_token(nbf=int(time.time()) + 120), id="not-yet-valid"),
        pytest.param(make_token(exp=None), id="missing-exp"),
        pytest.param(make_token(sub=None), id="missing-sub"),
        pytest.param(make_token(key=OTHER_KEY), id="bad-signature"),
        pytest.param(make_token(kid="unknown"), id="unknown-kid"),
        pytest.param(make_token(kid=None), id="missing-kid"),
        pytest.param(
            jwt.encode({"sub": "x"}, "secret-secret-secret-secret-1234", "HS256"),
            id="hs256",
        ),
        pytest.param("not-a-jwt", id="garbage"),
    ],
)
def test_invalid_tokens_raise_401(token):
    with pytest.raises(InvalidToken) as error:
        make_verifier().verify(token)
    assert error.value.status_code == 401


def test_expiry_within_clock_skew_is_accepted():
    token = make_token(exp=int(time.time()) - 10)
    assert make_verifier().verify(token).subject == "user-1"


def test_alg_none_is_rejected():
    token = jwt.encode({"sub": "x", "iss": ISSUER}, None, algorithm="none")
    with pytest.raises(InvalidToken):
        make_verifier().verify(token)


def test_jwks_source_refreshes_once_per_window(monkeypatch):
    from lib_management.identity.auth import JwksKeySource

    source = JwksKeySource("http://keycloak.test/certs", min_refresh_seconds=30)
    calls = []

    def fake_refresh():
        calls.append(1)
        source._fetched_at = time.monotonic()

    monkeypatch.setattr(source, "_refresh", fake_refresh)
    assert source.get("random-1") is None
    assert source.get("random-2") is None
    assert len(calls) == 1
