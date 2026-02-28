"""Gateway helpers for MCP tool dispatch."""

from __future__ import annotations

from typing import Any

from app.mcp_tooling import call_tool_by_name, register_tools


def initialize_gateway(mcp: Any) -> dict[str, Any]:
    """Initialize gateway state by registering the canonical tool set."""
    return register_tools(mcp)


def dispatch_tool_request(
    tool_name: str,
    arguments: dict[str, Any] | None,
    authorization_header: str | None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Dispatch through canonical tool invocation logic."""
    return call_tool_by_name(
        tool_name=tool_name,
        arguments=arguments,
        authorization_header=authorization_header,
        request_id=request_id,
    )
