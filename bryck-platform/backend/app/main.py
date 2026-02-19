from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import (
    BryckAPIUnavailableError,
    MachineAlreadyDecommissionedError,
    MachineIPConflictError,
    MachineNotFoundError,
)

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ── CORS ──────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────
app.include_router(api_router)


# ── Health probe ──────────────────────────────
@app.get("/health", tags=["System"], summary="Liveness probe")
async def health():
    return {"status": "ok", "version": settings.APP_VERSION}
