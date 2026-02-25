import socket
import pytest


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    """Block accidental network access to keep tests deterministic/offline."""

    real_connect = socket.socket.connect

    def guarded_connect(self, address):  # pragma: no cover - behavior assertion in tests
        host, *_ = address
        if host in {"127.0.0.1", "::1", "localhost"}:
            return real_connect(self, address)
        raise RuntimeError(f"Network disabled during tests: attempted {address!r}")

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
