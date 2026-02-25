"""Regression test for startup import path."""

from orchestrator.api import app


def test_app_imports_for_startup() -> None:
    assert app is not None
