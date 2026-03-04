"""
routers/sessions.py

Data entry path: create a session, paste JDs into it, read it back out.
This is the first path that touches Postgres for real.

Endpoints:
    POST   /api/sessions              → create session
    POST   /api/sessions/{id}/jds     → add JD (auto-cleans, enforces 25-cap)
    GET    /api/sessions/{id}         → full session state with all JDs

Assumes:
    - database.py exports `get_session` (yields an AsyncSession)
    - models.py is at the package root
    - text_cleaning.py is at the package root

Not here yet (see service-layer-notes.md):
    - POST /sessions/{id}/analyze  (SSE, separate router)
    - Activity cascade             (services.py)
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ..database import get_session
from ..models import (
    JD,
    JDStatus,
    JDStatusSource,
    Session as SessionModel,
    SessionStatus,
    User,
)
from ..services.text_cleaning import clean_jd_text

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


# ── Auth stub ─────────────────────────────────────────────────────────────────
# Replace this with real cookie auth when you get there.
# For now it grabs the first user in the DB — enough to test the data path.

async def get_current_user(db: AsyncSession = Depends(get_session)) -> User:
    result = await db.execute(select(User))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=401, detail="No user found — seed one first")
    return user


# ── Request schemas ───────────────────────────────────────────────────────────

class SessionCreate(BaseModel):
    board: str                     # "LinkedIn", "Indeed", etc.
    filters: str                   # free text: "remote, last 24 hours"
    search_term: str               # the keyword used


class JDCreate(BaseModel):
    raw_text: str                  # the paste — required, everything else optional
    company: str = ""
    role: str = ""
    compensation: Optional[str] = None
    employee_count: Optional[str] = None
    link: Optional[str] = None


# ── Response schemas ──────────────────────────────────────────────────────────
# Separate from the SQLModel tables so we control what the API surface looks like.
# Extend these as the frontend needs more fields.

class JDRead(BaseModel):
    id: UUID
    session_id: UUID
    number: int
    company: str
    role: str
    compensation: Optional[str]
    employee_count: Optional[str]
    link: Optional[str]
    cleaned_text: str              # cleaned version — raw available via separate endpoint if needed
    status: JDStatus
    status_source: JDStatusSource
    analysis_text: Optional[str]
    cover_letter_requested: bool
    flagged_for_review: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionRead(BaseModel):
    id: UUID
    user_id: UUID
    board: str
    filters: str
    search_term: str
    meta_analysis: Optional[str]
    status: SessionStatus
    created_at: datetime
    jd_count: int                  # convenience — avoids a len() on the frontend

    model_config = {"from_attributes": True}


class SessionWithJDs(SessionRead):
    jds: list[JDRead]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
async def create_session(
    body: SessionCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> SessionRead:
    """
    Create a new search session. One session = one set of board/filters/search_term.
    If you change the search term, you make a new session — that's intentional
    (keeps funnel analytics clean, see ADR-006).
    """
    session = SessionModel(
        user_id=current_user.id,
        board=body.board.strip(),
        filters=body.filters.strip(),
        search_term=body.search_term.strip(),
        status=SessionStatus.active,
    )
    db.add(session)           # add() is sync even on AsyncSession — no await
    await db.commit()
    await db.refresh(session)

    return SessionRead(
        **session.model_dump(),
        jd_count=0,
    )


@router.post(
    "/{session_id}/jds",
    response_model=JDRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_jd(
    session_id: UUID,
    body: JDCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> JDRead:
    """
    Paste a JD into a session. Cleaning is applied automatically.

    Returns the cleaned JD — callers don't need to clean before sending.
    The raw paste is stored separately (JD.raw_text) for the "view raw" toggle.

    Errors:
        404  session not found or doesn't belong to current user
        409  session already has 25 JDs (the cap)
        422  validation error (raw_text empty, etc.)
    """
    # ── Ownership check ───────────────────────────────────────────────────────
    session = await db.get(SessionModel, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    # ── 25-JD cap (API layer, not DB) ─────────────────────────────────────────
    result = await db.execute(select(JD).where(JD.session_id == session_id))
    existing = result.scalars().all()
    if len(existing) >= 25:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Session is full (max 25 JDs). Start a new session to continue.",
        )

    # ── Clean and store ───────────────────────────────────────────────────────
    raw = body.raw_text
    cleaned = clean_jd_text(raw)

    if not cleaned:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="raw_text was empty after cleaning",
        )

    jd = JD(
        session_id=session_id,
        number=len(existing) + 1,   # 1-indexed, maps to job board order
        raw_text=raw,
        cleaned_text=cleaned,
        company=body.company.strip(),
        role=body.role.strip(),
        compensation=body.compensation,
        employee_count=body.employee_count,
        link=body.link,
        status=JDStatus.pending,
        status_source=JDStatusSource.ai,
    )
    db.add(jd)
    await db.commit()
    await db.refresh(jd)

    return JDRead.model_validate(jd)


@router.get("/{session_id}", response_model=SessionWithJDs)
async def get_session_with_jds(
    session_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> SessionWithJDs:
    """
    Full session state with all JDs, ordered by number (job board order).
    This is the main read path — the frontend polls this after batch analysis
    to pick up updated statuses and analysis text.
    """
    session = await db.get(SessionModel, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    result = await db.execute(
        select(JD)
        .where(JD.session_id == session_id)
        .order_by(JD.number)
    )
    jds = result.scalars().all()

    return SessionWithJDs(
        **session.model_dump(),
        jd_count=len(jds),
        jds=[JDRead.model_validate(jd) for jd in jds],
    )
