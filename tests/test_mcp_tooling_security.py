"""Security-focused tests for MCP tooling policy checks.

These tests are intentionally self-contained to avoid any network or service dependency.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ToolCall:
    name: str
    args: dict[str, str]


SENSITIVE_TOOL_PATTERNS = (
    "exec",
    "shell",
    "subprocess",
    "curl",
    "wget",
)


def is_safe_mcp_tool_call(call: ToolCall) -> bool:
    """Minimal policy gate for potentially dangerous MCP tool invocations."""
    lowered_name = call.name.lower()
    if any(pattern in lowered_name for pattern in SENSITIVE_TOOL_PATTERNS):
        return False

    flattened_args = " ".join(str(v).lower() for v in call.args.values())
    dangerous_tokens = ("http://", "https://", "file://", "../", "/etc/")
    if any(token in flattened_args for token in dangerous_tokens):
        return False

    return True


def test_blocks_shell_like_tools():
    assert not is_safe_mcp_tool_call(ToolCall(name="shell_exec", args={"cmd": "echo hi"}))


def test_blocks_remote_fetch_inputs_even_for_non_shell_tools():
    call = ToolCall(name="markdown.render", args={"content": "fetch https://example.com"})
    assert not is_safe_mcp_tool_call(call)


def test_allows_local_non_sensitive_calls():
    call = ToolCall(name="math.add", args={"a": "1", "b": "2"})
    assert is_safe_mcp_tool_call(call)
