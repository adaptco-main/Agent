import warnings

import pytest

from agents.tester import run_tester_flow
from orchestrator.llm_util import call_llm


def test_tester_flow_accepts_expected_payload():
    result = run_tester_flow({"intent": "check deployment health"})

    assert result["status"] == "ok"
    assert result["intent"] == "check deployment health"
    assert result["llm"]["ok"] is True
    assert result["llm"]["prompt"] == "check deployment health"


@pytest.mark.parametrize(
    "payload, message",
    [
        (None, "payload must be an object"),
        ({}, "payload missing required field(s): intent"),
        ({"intent": ""}, "payload.intent must be a non-empty string"),
        ({"intent": "   "}, "payload.intent must be a non-empty string"),
        ({"intent": 123}, "payload.intent must be a non-empty string"),
    ],
)
def test_tester_flow_rejects_malformed_payload(payload, message):
    import re
    with pytest.raises(ValueError, match=re.escape(message)):
        run_tester_flow(payload)


def test_call_llm_backward_compatibility_emits_deprecation_warning():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = call_llm(prompt_intent="legacy prompt")

    assert result["prompt"] == "legacy prompt"
    assert any(issubclass(w.category, DeprecationWarning) for w in caught)


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({}, "`prompt` is required."),
        (
            {"prompt": "new", "prompt_intent": "old"},
            "Provide only one of `prompt` or deprecated `prompt_intent`.",
        ),
        ({"prompt": ""}, "`prompt` must be a non-empty string."),
    ],
)
def test_call_llm_rejects_invalid_argument_shapes(kwargs, message):
    import re
    with pytest.raises(ValueError, match=re.escape(message)):
        call_llm(**kwargs)
