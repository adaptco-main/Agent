"""Application entrypoint."""

from __future__ import annotations

from typing import Any

from orchestrator.webhook import router as webhook_router

try:  # pragma: no cover - exercised where fastapi is installed
    from fastapi import FastAPI
except Exception:  # pragma: no cover - fallback for minimal environments
    class FastAPI:  # type: ignore[override]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.routers: list[Any] = []

        def include_router(self, router: Any) -> None:
            self.routers.append(router)


app = FastAPI(title="orchestrator")
app.include_router(webhook_router)
