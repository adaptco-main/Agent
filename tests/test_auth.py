import hashlib
import hmac
import time

from fastapi.testclient import TestClient

from orchestrator.api import app as orchestrator_app
from rbac.rbac_service import app as rbac_app


def _sig(secret: str, method: str, path: str, timestamp: int, body: bytes = b"") -> str:
    body_hash = hashlib.sha256(body).hexdigest()
    payload = f"{method}\n{path}\n{timestamp}\n{body_hash}"
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


def test_orchestrate_requires_bearer(monkeypatch):
    monkeypatch.setenv("ORCHESTRATOR_BEARER_TOKEN", "token-123")
    client = TestClient(orchestrator_app)

    assert client.post("/orchestrate").status_code == 401
    assert client.post("/orchestrate", headers={"Authorization": "Bearer wrong"}).status_code == 403
    assert client.post("/orchestrate", headers={"Authorization": "Bearer token-123"}).status_code == 200


def test_plans_require_bearer(monkeypatch):
    monkeypatch.setenv("ORCHESTRATOR_BEARER_TOKEN", "token-123")
    client = TestClient(orchestrator_app)

    assert client.get("/plans/a").status_code == 401
    assert client.get("/plans/a", headers={"Authorization": "Bearer wrong"}).status_code == 403
    assert client.get("/plans/a", headers={"Authorization": "Bearer token-123"}).status_code == 200


def test_rbac_signature_required_and_valid(monkeypatch):
    monkeypatch.setenv("RBAC_SECRET", "super-secret")
    client = TestClient(rbac_app)

    endpoints = [("POST", "/onboarding"), ("POST", "/verify"), ("GET", "/list"), ("POST", "/admin/grant")]
    for method, path in endpoints:
        response = client.request(method, path)
        assert response.status_code == 401

        ts = int(time.time())
        bad_headers = {
            "X-Service-Id": "svc-b",
            "X-Timestamp": str(ts),
            "X-Signature": "bad",
        }
        response = client.request(method, path, headers=bad_headers)
        assert response.status_code == 403

        sig = _sig("super-secret", method, path, ts)
        headers = {
            "X-Service-Id": "svc-b",
            "X-Timestamp": str(ts),
            "X-Signature": sig,
        }
        response = client.request(method, path, headers=headers)
        assert response.status_code == 200


def test_rbac_replay_rejected(monkeypatch):
    monkeypatch.setenv("RBAC_SECRET", "super-secret")
    client = TestClient(rbac_app)

    ts = int(time.time())
    sig = _sig("super-secret", "POST", "/verify", ts)
    headers = {
        "X-Service-Id": "svc-c",
        "X-Timestamp": str(ts),
        "X-Signature": sig,
    }
    assert client.post("/verify", headers=headers).status_code == 200
    assert client.post("/verify", headers=headers).status_code == 403
