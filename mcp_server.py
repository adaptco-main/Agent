"""MCP server bootstrap."""

from __future__ import annotations

from typing import Any

from app.mcp_tooling import register_tools


class MCPServer:
    def __init__(self, mcp: Any) -> None:
        self.mcp = mcp
        self.registry = register_tools(self.mcp)


def create_server(mcp: Any) -> MCPServer:
    return MCPServer(mcp)
