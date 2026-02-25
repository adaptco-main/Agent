"""Offline deterministic tests for OIDC token validation rules."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time


SECRET = b"unit-test-secret"


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def build_jwt(claims: dict) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    encoded_header = _b64url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    encoded_claims = _b64url(json.dumps(claims, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{encoded_header}.{encoded_claims}".encode("utf-8")
    signature = hmac.new(SECRET, signing_input, hashlib.sha256).digest()
    return f"{encoded_header}.{encoded_claims}.{_b64url(signature)}"


def validate_oidc_token(token: str, issuer: str, audience: str, now: int | None = None) -> bool:
    now = int(time.time() if now is None else now)

    encoded_header, encoded_claims, encoded_sig = token.split(".")
    signing_input = f"{encoded_header}.{encoded_claims}".encode("utf-8")
    expected_sig = _b64url(hmac.new(SECRET, signing_input, hashlib.sha256).digest())
    if not hmac.compare_digest(encoded_sig, expected_sig):
        return False

    claims_raw = base64.urlsafe_b64decode(encoded_claims + "=")
    claims = json.loads(claims_raw.decode("utf-8"))

    if claims.get("iss") != issuer:
        return False
    if claims.get("aud") != audience:
        return False
    if int(claims.get("exp", 0)) < now:
        return False

    return True


def test_accepts_valid_token_with_matching_iss_aud_and_exp():
    now = 2_000_000_000
    token = build_jwt(
        {
            "iss": "https://issuer.internal",
            "aud": "agent-mesh",
            "sub": "user-123",
            "exp": now + 300,
        }
    )

    assert validate_oidc_token(token, "https://issuer.internal", "agent-mesh", now=now)


def test_rejects_wrong_audience_even_with_valid_signature():
    now = 2_000_000_000
    token = build_jwt(
        {
            "iss": "https://issuer.internal",
            "aud": "different-aud",
            "sub": "user-123",
            "exp": now + 300,
        }
    )

    assert not validate_oidc_token(token, "https://issuer.internal", "agent-mesh", now=now)


def test_rejects_expired_token_even_with_valid_signature():
    now = 2_000_000_000
    token = build_jwt(
        {
            "iss": "https://issuer.internal",
            "aud": "agent-mesh",
            "sub": "user-123",
            "exp": now - 1,
        }
    )

    assert not validate_oidc_token(token, "https://issuer.internal", "agent-mesh", now=now)
