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
from .routers import sessions
app.include_router(sessions.router)  # prefix lives in the router itself ("/api/sessions")
# app.include_router(jds.router,      prefix="/api/jds",      tags=["jds"])
# app.include_router(resumes.router,  prefix="/api/resumes",  tags=["resumes"])
# app.include_router(activities.router, prefix="/api/activities", tags=["activities"])


if __name__ == "__main__":
    # ── Dev seed: python -m app.main ─────────────────────────────────────────────
    import asyncio
    from .database import AsyncSessionLocal
    from .models import User

    async def seed():
        async with AsyncSessionLocal() as db:
            user = User(auth_token="test-token")
            db.add(user)
            await db.commit()
            print("Seeded test user.")

    asyncio.run(seed())

    """
    What to check:
    ----------------
    Go to http://localhost:8000/docs — Swagger UI, everything is clickable. Hit the endpoints in order:

    POST /api/sessions — create a session, copy the id from the response
    POST /api/sessions/{id}/jds — paste a real JD in raw_text, use the session id
    GET /api/sessions/{id} — confirm the JD came back cleaned and numbered correctly

    What to verify on that GET:

    raw_text ≠ cleaned_text if you pasted something messy (try copying a LinkedIn JD — you'll get \xa0s for free)
    number is 1
    status is pending, status_source is ai
    jd_count is 1

    If Postgres isn't running locally yet, docker compose up -d db (or Railway's dev DB) before step 2.
    """