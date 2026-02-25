"""Lightweight metrics helpers used by webhook handlers.

This module intentionally keeps metric collection as no-ops so importing
application modules never fails in environments where a metrics backend is not
configured.
"""

from __future__ import annotations

from collections import defaultdict
from threading import Lock

_LOCK = Lock()
_COUNTERS: dict[str, int] = defaultdict(int)
_DURATIONS: dict[str, list[float]] = defaultdict(list)


def _inc(name: str, value: int = 1) -> None:
    with _LOCK:
        _COUNTERS[name] += value


def _observe(name: str, value: float) -> None:
    with _LOCK:
        _DURATIONS[name].append(value)


def record_webhook_received(event_type: str | None = None) -> None:
    """Record that a webhook request was received."""
    _inc("webhook.received")
    if event_type:
        _inc(f"webhook.received.{event_type}")


def record_webhook_processed(
    event_type: str | None = None,
    *,
    success: bool = True,
    duration_seconds: float | None = None,
) -> None:
    """Record webhook processing outcome and optional latency."""
    _inc("webhook.processed")
    _inc("webhook.success" if success else "webhook.failure")
    if event_type:
        _inc(f"webhook.processed.{event_type}")
    if duration_seconds is not None:
        _observe("webhook.duration_seconds", duration_seconds)
