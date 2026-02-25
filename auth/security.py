import hashlib
import hmac
import os
import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Iterable

from fastapi import HTTPException, Request


class ReplayCache:
    """In-memory replay cache with TTL cleanup."""

    def __init__(self) -> None:
        self._seen: dict[str, float] = {}
        self._lock = Lock()

    def check_and_store(self, key: str, ttl_seconds: int) -> bool:
        now = time.time()
        with self._lock:
            self._seen = {k: exp for k, exp in self._seen.items() if exp > now}
            if key in self._seen:
                return False
            self._seen[key] = now + ttl_seconds
        return True


replay_cache = ReplayCache()


def require_bearer(request: Request) -> str:
    expected = os.getenv("ORCHESTRATOR_BEARER_TOKEN", "change-me")
    authz = request.headers.get("authorization")
    if not authz:
        raise HTTPException(status_code=401, detail="Missing bearer token")

    parts = authz.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid auth scheme")

    token = parts[1]
    if not hmac.compare_digest(token, expected):
        raise HTTPException(status_code=403, detail="Invalid bearer token")
    return token


@dataclass(slots=True)
class ServiceSignatureVerifier:
    secret_env: str = "RBAC_SECRET"
    allowed_clock_skew_seconds: int = 300
    replay_ttl_seconds: int = 300
    required_headers: Iterable[str] = field(
        default_factory=lambda: ("x-service-id", "x-timestamp", "x-signature")
    )

    async def __call__(self, request: Request) -> str:
        missing = [h for h in self.required_headers if not request.headers.get(h)]
        if missing:
            raise HTTPException(status_code=401, detail=f"Missing headers: {', '.join(missing)}")

        timestamp_raw = request.headers["x-timestamp"]
        try:
            timestamp = int(timestamp_raw)
        except ValueError as exc:
            raise HTTPException(status_code=401, detail="Invalid timestamp") from exc

        now = int(time.time())
        if abs(now - timestamp) > self.allowed_clock_skew_seconds:
            raise HTTPException(status_code=403, detail="Timestamp outside allowed window")

        body = await request.body()
        body_hash = hashlib.sha256(body).hexdigest()
        signing_string = f"{request.method}\n{request.url.path}\n{timestamp_raw}\n{body_hash}"

        secret = os.getenv(self.secret_env)
        if not secret:
            raise HTTPException(status_code=500, detail=f"Missing server secret: {self.secret_env}")

        expected_sig = hmac.new(secret.encode(), signing_string.encode(), hashlib.sha256).hexdigest()
        provided_sig = request.headers["x-signature"]
        if not hmac.compare_digest(provided_sig, expected_sig):
            raise HTTPException(status_code=403, detail="Invalid signature")

        replay_key = f"{request.headers['x-service-id']}:{timestamp_raw}:{provided_sig}"
        if not replay_cache.check_and_store(replay_key, self.replay_ttl_seconds):
            raise HTTPException(status_code=403, detail="Replay detected")

        return request.headers["x-service-id"]


require_service_signature = ServiceSignatureVerifier()
