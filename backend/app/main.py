"""
ApplicationPipeline — FastAPI entry point.

Phase 0, Sprint 11. Backend is functional: session/JD CRUD, resume CRUD,
Claude batch analysis (SSE), parallel tailoring with docx generation,
skip-already-tailored logic, batch status dashboards, zip downloads.
Frontend: full session flow, SSE card animations, resume management,
tailoring UI with polling and output display.
"""
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await create_db_and_tables()
    yield


app = FastAPI(
    title="ApplicationPipeline",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "environment": settings.environment}


# ── Routers ───────────────────────────────────────────────────────────────────
from .routers import sessions, jds, resumes
app.include_router(sessions.router)
app.include_router(jds.router)
app.include_router(resumes.router)


# ── SPA static serving (production only) ─────────────────────────────────────
# In dev, this directory doesn't exist — Vite proxy handles the frontend.
# In production, the Dockerfile copies the built React app into /app/static/.
_static_dir = Path(__file__).resolve().parent.parent / "static"

if _static_dir.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=_static_dir / "assets"),
        name="static-assets",
    )

    @app.get("/{full_path:path}")
    async def _serve_spa(full_path: str):
        file_path = _static_dir / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(_static_dir / "index.html")