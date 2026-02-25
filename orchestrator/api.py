from fastapi import Depends, FastAPI

from auth.security import require_bearer

app = FastAPI(title="orchestrator")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/orchestrate", dependencies=[Depends(require_bearer)])
def orchestrate() -> dict[str, str]:
    return {"status": "started"}


@app.get("/plans/{plan_id}", dependencies=[Depends(require_bearer)])
def get_plan(plan_id: str) -> dict[str, str]:
    return {"plan_id": plan_id, "status": "ready"}
