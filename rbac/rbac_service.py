import os

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth.security import require_service_signature

app = FastAPI(title="rbac-service")

allowed_origins_env = os.getenv("RBAC_ALLOWED_ORIGINS", "")
allowed_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
if allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "X-Service-Id", "X-Timestamp", "X-Signature"],
    )


@app.post("/onboarding", dependencies=[Depends(require_service_signature)])
def onboarding() -> dict[str, str]:
    return {"status": "onboarded"}


@app.post("/verify", dependencies=[Depends(require_service_signature)])
def verify() -> dict[str, str]:
    return {"verified": "true"}


@app.get("/list", dependencies=[Depends(require_service_signature)])
def list_roles() -> dict[str, list[str]]:
    return {"roles": ["reader", "admin"]}


@app.post("/admin/grant", dependencies=[Depends(require_service_signature)])
def admin_grant() -> dict[str, str]:
    return {"status": "granted"}
