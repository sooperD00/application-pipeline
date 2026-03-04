"""
ApplicationPipeline — FastAPI entry point.

Phase 0: skeleton with health check and stub routers.
Nothing works yet, but you have a live endpoint and a real database.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


# ── Routers (stub imports — uncomment as you build each) ──────────────────────
# from .routers import sessions, jds, resumes, activities
# app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
# app.include_router(jds.router,      prefix="/api/jds",      tags=["jds"])
# app.include_router(resumes.router,  prefix="/api/resumes",  tags=["resumes"])
# app.include_router(activities.router, prefix="/api/activities", tags=["activities"])