"""Canonical MCP tool registration and dispatch utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


class ToolError(Exception):
    """Base exception for tool dispatch failures."""

    code = "tool_error"

    def __init__(self, message: str, *, details: Any | None = None) -> None:
        super().__init__(message)
        self.details = details


class ToolNotFoundError(ToolError):
    code = "tool_not_found"


class InvalidArgumentsError(ToolError):
    code = "invalid_arguments"


class UnauthorizedError(ToolError):
    code = "unauthorized"


@dataclass(frozen=True)
class ToolSpec:
    name: str
    handler: Callable[..., Any]
    validator: Callable[[dict[str, Any]], None]


_TOOL_REGISTRY: dict[str, Callable[..., Any]] = {}
_VALIDATORS: dict[str, Callable[[dict[str, Any]], None]] = {}


def _validate_echo(arguments: dict[str, Any]) -> None:
    if not isinstance(arguments, dict):
        raise InvalidArgumentsError("arguments must be an object")
    message = arguments.get("message")
    if not isinstance(message, str) or not message:
        raise InvalidArgumentsError("'message' must be a non-empty string")


def _validate_health(arguments: dict[str, Any]) -> None:
    if arguments is None:
        return
    if not isinstance(arguments, dict):
        raise InvalidArgumentsError("arguments must be an object")


def _tool_echo(*, message: str, **_: Any) -> dict[str, str]:
    return {"message": message}


def _tool_health_check(**_: Any) -> dict[str, str]:
    return {"status": "ok"}


def _tool_specs() -> tuple[ToolSpec, ...]:
    return (
        ToolSpec(name="echo", handler=_tool_echo, validator=_validate_echo),
        ToolSpec(name="health.check", handler=_tool_health_check, validator=_validate_health),
    )


def _register_with_mcp(mcp: Any, spec: ToolSpec) -> None:
    """Register a tool to any MCP object that supports decorator or direct registration styles."""
    if hasattr(mcp, "tool") and callable(getattr(mcp, "tool")):
        decorator = mcp.tool(spec.name)
        decorator(spec.handler)
    elif hasattr(mcp, "register_tool") and callable(getattr(mcp, "register_tool")):
        mcp.register_tool(spec.name, spec.handler)


def register_tools(mcp: Any) -> dict[str, Callable[..., Any]]:
    """Register all MCP tools and return the canonical runtime registry."""
    _TOOL_REGISTRY.clear()
    _VALIDATORS.clear()

    for spec in _tool_specs():
        _TOOL_REGISTRY[spec.name] = spec.handler
        _VALIDATORS[spec.name] = spec.validator
        _register_with_mcp(mcp, spec)

    return dict(_TOOL_REGISTRY)


def _enforce_authorization(tool_name: str, authorization_header: str | None, arguments: dict[str, Any]) -> None:
    del tool_name, arguments
    if not authorization_header or not authorization_header.startswith("Bearer "):
        raise UnauthorizedError("Missing or invalid authorization header")


def _error_envelope(*, request_id: str | None, tool_name: str, error: ToolError) -> dict[str, Any]:
    return {
        "ok": False,
        "request_id": request_id,
        "tool_name": tool_name,
        "error": {
            "code": error.code,
            "message": str(error),
            "details": error.details,
        },
    }


def call_tool_by_name(
    tool_name: str,
    arguments: dict[str, Any] | None,
    authorization_header: str | None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Dispatch a tool by name with validation, auth, and stable envelopes."""
    args = arguments if arguments is not None else {}

    try:
        if tool_name not in _TOOL_REGISTRY:
            raise ToolNotFoundError(f"Unknown MCP tool: {tool_name}")

        validator = _VALIDATORS[tool_name]
        validator(args)
        _enforce_authorization(tool_name, authorization_header, args)

        result = _TOOL_REGISTRY[tool_name](**args)
        return {
            "ok": True,
            "request_id": request_id,
            "tool_name": tool_name,
            "result": result,
        }
    except ToolError as error:
        return _error_envelope(request_id=request_id, tool_name=tool_name, error=error)
