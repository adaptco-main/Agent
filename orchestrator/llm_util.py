"""LLM utility helpers used by orchestration and agents."""

from __future__ import annotations

import warnings
from typing import Any, Callable, Dict, Optional


LLMCallable = Callable[[str], str]
PROMPT_INTENT_DEPRECATION_VERSION = "2.0"
PROMPT_INTENT_DEPRECATION_MESSAGE = (
    "`prompt_intent` is deprecated and will be removed in "
    f"{PROMPT_INTENT_DEPRECATION_VERSION}; use `prompt`."
)


def call_llm(
    *,
    prompt: Optional[str] = None,
    prompt_intent: Optional[str] = None,
    llm_client: Optional[LLMCallable] = None,
) -> Dict[str, Any]:
    """Call the configured LLM and return a normalized payload.

    Deprecation path for ``prompt_intent``:
    - Supported for backward compatibility in current releases.
    - Emits ``DeprecationWarning`` on use.
    - Planned removal in version 2.0.
    """

    if prompt is not None and prompt_intent is not None:
        raise ValueError("Provide only one of `prompt` or deprecated `prompt_intent`.")

    if prompt is None:
        if prompt_intent is None:
            raise ValueError("`prompt` is required.")
        warnings.warn(
            PROMPT_INTENT_DEPRECATION_MESSAGE,
            DeprecationWarning,
            stacklevel=2,
        )
        prompt = prompt_intent

    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("`prompt` must be a non-empty string.")

    runner = llm_client or (lambda p: f"stub:{p}")
    content = runner(prompt)
    if not isinstance(content, str):
        raise ValueError("LLM client must return a string response.")

    return {"ok": True, "prompt": prompt, "content": content}
