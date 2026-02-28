"""Tester flow for validating and executing lightweight LLM checks."""

from __future__ import annotations

from typing import Any, Dict

from orchestrator.llm_util import call_llm


REQUIRED_PAYLOAD_FIELDS = ("intent",)


def run_tester_flow(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Validate tester payload and execute the LLM call."""

    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")

    missing = [field for field in REQUIRED_PAYLOAD_FIELDS if field not in payload]
    if missing:
        raise ValueError(f"payload missing required field(s): {', '.join(missing)}")

    intent = payload["intent"]
    if not isinstance(intent, str) or not intent.strip():
        raise ValueError("payload.intent must be a non-empty string")

    # Use the modern argument name; `prompt_intent` support remains in llm_util
    llm_result = call_llm(prompt=intent)

    return {
        "status": "ok",
        "intent": intent,
        "llm": llm_result,
    }
