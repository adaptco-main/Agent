from __future__ import annotations

from typing import Any

from app import mcp_gateway
from app.mcp_tooling import call_tool_by_name, register_tools
from mcp_server import create_server


class FakeMCP:
    def __init__(self) -> None:
        self.registered: dict[str, Any] = {}

    def tool(self, name: str):
        def decorator(fn):
            self.registered[name] = fn
            return fn

        return decorator


def _setup_registry() -> dict[str, Any]:
    return register_tools(FakeMCP())


def test_registration_parity_between_gateway_and_server() -> None:
    mcp_a = FakeMCP()
    gateway_registry = mcp_gateway.initialize_gateway(mcp_a)

    mcp_b = FakeMCP()
    server = create_server(mcp_b)

    assert set(gateway_registry.keys()) == set(server.registry.keys())
    assert set(mcp_a.registered.keys()) == set(mcp_b.registered.keys())


def test_dispatch_known_tool_success() -> None:
    _setup_registry()

    response = call_tool_by_name(
        tool_name="echo",
        arguments={"message": "hello"},
        authorization_header="Bearer token",
        request_id="req-1",
    )

    assert response == {
        "ok": True,
        "request_id": "req-1",
        "tool_name": "echo",
        "result": {"message": "hello"},
    }


def test_dispatch_unknown_tool() -> None:
    _setup_registry()

    response = call_tool_by_name(
        tool_name="does.not.exist",
        arguments={},
        authorization_header="Bearer token",
        request_id="req-2",
    )

    assert response["ok"] is False
    assert response["request_id"] == "req-2"
    assert response["error"]["code"] == "tool_not_found"


def test_dispatch_invalid_args() -> None:
    _setup_registry()

    response = call_tool_by_name(
        tool_name="echo",
        arguments={"message": ""},
        authorization_header="Bearer token",
        request_id="req-3",
    )

    assert response["ok"] is False
    assert response["request_id"] == "req-3"
    assert response["error"]["code"] == "invalid_arguments"


def test_dispatch_unauthorized() -> None:
    _setup_registry()

    response = call_tool_by_name(
        tool_name="echo",
        arguments={"message": "hello"},
        authorization_header=None,
        request_id="req-4",
    )

    assert response["ok"] is False
    assert response["request_id"] == "req-4"
    assert response["error"]["code"] == "unauthorized"
