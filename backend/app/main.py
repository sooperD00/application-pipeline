"""
ApplicationPipeline — FastAPI entry point.

Deployed to Railway. Backend: session/JD CRUD, resume CRUD,
Claude batch analysis (SSE), parallel tailoring with docx generation,
skip-already-tailored logic, batch status dashboards, zip downloads.
Cookie-based anonymous auth (get_current_user in sessions.py).
Frontend: full session flow, SSE card animations, resume management,
tailoring UI with polling and output display. SPA static serving below.
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


def _spa_file(static_dir: Path, full_path: str) -> Path:
    """The file to send for a request path: a real file inside static_dir, else index.html.

    Resolves before checking, so a path that climbs out with "..", names an absolute path
    ("//etc/passwd" arrives as "/etc/passwd", and pathlib lets an absolute right-hand side
    replace the left), or follows a symlink out of static_dir gets index.html instead.
    """
    root = static_dir.resolve()
    try:
        candidate = (root / full_path).resolve()
        if candidate.is_relative_to(root) and candidate.is_file():
            return candidate
    except (OSError, ValueError):  # ValueError: an embedded NUL byte from %00
        pass
    return root / "index.html"


if _static_dir.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=_static_dir / "assets"),
        name="static-assets",
    )

    @app.get("/{full_path:path}")
    async def _serve_spa(full_path: str):
        return FileResponse(_spa_file(_static_dir, full_path))