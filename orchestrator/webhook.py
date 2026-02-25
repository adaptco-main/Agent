"""Webhook router definitions."""

from __future__ import annotations

from time import perf_counter
from typing import Any

from orchestrator.metrics import record_webhook_processed, record_webhook_received

try:  # pragma: no cover - exercised where fastapi is installed
    from fastapi import APIRouter
except Exception:  # pragma: no cover - fallback for minimal environments
    class APIRouter:  # type: ignore[override]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.routes: list[Any] = []

        def post(self, *args: Any, **kwargs: Any):
            def decorator(func: Any) -> Any:
                self.routes.append(func)
                return func

            return decorator


router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.post("/")
async def receive_webhook(payload: dict[str, Any]) -> dict[str, str]:
    """Receive and acknowledge webhook payloads."""
    event_type = payload.get("type") if isinstance(payload, dict) else None
    start = perf_counter()
    record_webhook_received(event_type)
    try:
        # Placeholder for domain processing logic.
        return {"status": "ok"}
    finally:
        record_webhook_processed(
            event_type,
            success=True,
            duration_seconds=perf_counter() - start,
        )
