"""
routers/sessions.py

Session and JD data entry, plus the analysis kickoff and batch tailoring.

Endpoints:
    GET    /api/sessions              → list all sessions for current user (Sprint 6)
    POST   /api/sessions              → create session
    POST   /api/sessions/{id}/jds     → add JD (auto-cleans, enforces 25-cap)
    GET    /api/sessions/{id}         → full session state with all JDs
    POST   /api/sessions/{id}/analyze → kick off batch analysis (SSE stream)
    POST   /api/sessions/{id}/batch-tailor → tailoring for all Apply JDs (Sprint 5)
                                         + skip-completed logic (Sprint 6)
    GET    /api/sessions/{id}/tailoring-jobs → batch status dashboard (Sprint 6)

Assumes:
    - database.py exports `get_session` (yields an AsyncSession)
    - models.py is at the package root
    - services/claude.py, services/analysis.py, services/tailoring.py exist
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.background import BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
from sqlmodel import select

from ..config import settings
from ..database import get_session
from ..models import (
    JD,
    JDStatus,
    JDStatusSource,
    Resume,
    Session as SessionModel,
    SessionStatus,
    TailoringJob,
    TailoringStatus,
    User,
)
from ..services.text_cleaning import clean_jd_text
from ..services.analysis import stream_analysis
from ..services.tailoring import MAX_RESUMES, run_batch_tailor

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


class TailoringJobDashboardRead(BaseModel):
    """
    Tailoring job with JD context for the batch status dashboard (Sprint 6).
    Richer than TailoringJobRead — includes company and role so the frontend
    can label cards without a second round-trip.
    """
    id: UUID
    jd_id: UUID
    resume_id: UUID
    status: TailoringStatus
    output_resume: Optional[str]
    output_cover_letter: Optional[str]
    output_app_answers: Optional[Any] = None
    has_docx: bool
    model_used: str
    created_at: datetime
    completed_at: Optional[datetime]
    # JD context for dashboard labeling
    company: str
    role: str
    jd_number: int

    model_config = {"from_attributes": True}


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


@router.get("", response_model=list[SessionRead])
async def list_sessions(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[SessionRead]:
    """
    List all sessions for the current user, newest first.

    Each entry includes jd_count so the session picker can show how many
    JDs are in each session without loading them all. This is the
    prerequisite for the frontend session picker (Sprint 7).
    """
    # Scalar subquery: count JDs per session without N+1
    jd_count_subq = (
        select(func.count(JD.id))
        .where(JD.session_id == SessionModel.id)
        .correlate(SessionModel)
        .scalar_subquery()
    )

    result = await db.execute(
        select(SessionModel, jd_count_subq.label("jd_count"))
        .where(SessionModel.user_id == current_user.id)
        .order_by(SessionModel.created_at.desc())
    )
    rows = result.all()

    return [
        SessionRead(**s.model_dump(), jd_count=cnt)
        for s, cnt in rows
    ]


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


@router.post("/{session_id}/analyze")
async def analyze_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Kick off batch analysis for all JDs in a session.
    Returns a Server-Sent Events stream — keep the connection open.

    Events (in order): batch_start, jd_result (×N), batch_complete,
    then repeats for each batch of 5, then analysis_complete.
    On failure after one retry: error event, session reset to active.

    See architecture.md for the full event schema and payload shapes.

    Errors (before streaming starts):
        404  session not found or doesn't belong to current user
        409  analysis already in progress for this session
        422  session has no JDs to analyze
    """
    # Validate before starting the stream — once we return 200 and start
    # streaming we can no longer send HTTP error codes, so catch bad states here.
    session = await db.get(SessionModel, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status == SessionStatus.analyzing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Analysis already in progress for this session.",
        )

    jd_check = await db.execute(select(JD).where(JD.session_id == session_id))
    if not jd_check.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Session has no JDs. Add some JDs before analyzing.",
        )

    return StreamingResponse(
        stream_analysis(session_id, db, current_user),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # tells nginx (Railway's proxy) not to buffer the stream
        },
    )


# ── Tailoring dashboard ─────────────────────────────────────────────────────

@router.get(
    "/{session_id}/tailoring-jobs",
    response_model=list[TailoringJobDashboardRead],
)
async def list_session_tailoring_jobs(
    session_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[TailoringJobDashboardRead]:
    """
    All tailoring jobs across every JD in a session — the batch status dashboard.

    Returns jobs with JD company/role/number so the frontend can render
    status cards without a second round-trip. Ordered by JD number, then
    by job created_at desc (most recent attempt first within each JD).

    Tab 4 prerequisite (Sprint 9).

    Errors:
        404  Session not found or doesn't belong to current user
    """
    session = await db.get(SessionModel, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    result = await db.execute(
        select(TailoringJob, JD.company, JD.role, JD.number)
        .join(JD, TailoringJob.jd_id == JD.id)
        .where(JD.session_id == session_id)
        .order_by(JD.number, TailoringJob.created_at.desc())
    )
    rows = result.all()

    return [
        TailoringJobDashboardRead(
            id=job.id,
            jd_id=job.jd_id,
            resume_id=job.resume_id,
            status=job.status,
            output_resume=job.output_resume,
            output_cover_letter=job.output_cover_letter,
            output_app_answers=job.output_app_answers,
            has_docx=job.output_resume_docx is not None,
            model_used=job.model_used,
            created_at=job.created_at,
            completed_at=job.completed_at,
            company=company,
            role=role,
            jd_number=number,
        )
        for job, company, role, number in rows
    ]


# ── Batch tailoring ──────────────────────────────────────────────────────────

class BatchTailorJob(BaseModel):
    job_id: UUID
    jd_id: UUID

class BatchTailorResponse(BaseModel):
    jobs: list[BatchTailorJob]
    jd_count: int


@router.post(
    "/{session_id}/batch-tailor",
    response_model=BatchTailorResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def batch_tailor_session(
    session_id: UUID,
    background_tasks: BackgroundTasks,
    force: bool = Query(
        False,
        description="Re-tailor JDs that already have a completed job. "
                    "Default: skip them.",
    ),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> BatchTailorResponse:
    """
    Kick off tailoring for all Apply-status JDs in a session.

    All of the user's resumes (up to 3) are sent to Claude for each job.
    Jobs run in parallel, capped by settings.tailoring_parallelism (ADR-008).

    Sprint 6: JDs that already have a completed tailoring job (status=ready)
    are skipped unless force=true. This prevents accidental re-runs from
    burning API credits. The response only lists newly-created jobs.

    Returns 202 immediately with the list of job IDs. Frontend polls each
    via GET /jds/{jd_id}/tailoring/{job_id} for individual status.

    Errors:
        404  Session not found or doesn't belong to current user
        422  No resumes, too many resumes, or no Apply-status JDs
    """
    session = await db.get(SessionModel, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    # ── Resume cap check (hard limit = 3) ─────────────────────────────
    result = await db.execute(
        select(Resume)
        .where(Resume.user_id == current_user.id)
        .order_by(Resume.created_at.desc())
    )
    resumes = list(result.scalars().all())

    if not resumes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No resumes found. Create at least one resume before tailoring.",
        )
    if len(resumes) > MAX_RESUMES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Found {len(resumes)} resumes (max {MAX_RESUMES}). "
                "Delete extras before tailoring."
            ),
        )

    # ── Find all Apply JDs ────────────────────────────────────────────
    result = await db.execute(
        select(JD)
        .where(JD.session_id == session_id, JD.status == JDStatus.apply)
        .order_by(JD.number)
    )
    apply_jds = list(result.scalars().all())

    if not apply_jds:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No JDs with 'apply' status in this session.",
        )

    # ── Skip JDs that already have a completed job (Sprint 6) ─────────
    # Unless force=true, don't re-tailor JDs that already succeeded.
    if not force:
        already_done = await db.execute(
            select(TailoringJob.jd_id)
            .where(
                TailoringJob.jd_id.in_([jd.id for jd in apply_jds]),
                TailoringJob.status == TailoringStatus.ready,
            )
        )
        done_jd_ids = set(already_done.scalars().all())
        apply_jds = [jd for jd in apply_jds if jd.id not in done_jd_ids]

    if not apply_jds:
        # All JDs already have completed jobs — nothing to do
        return BatchTailorResponse(jobs=[], jd_count=0)

    # ── Create TailoringJob rows ──────────────────────────────────────
    # All resumes go in the prompt; resume_id FK uses most recent
    resume_id = resumes[0].id

    jobs: list[BatchTailorJob] = []

    for jd in apply_jds:
        job = TailoringJob(
            jd_id=jd.id,
            resume_id=resume_id,
            prompt_snapshot="",                  # filled by background task
            status=TailoringStatus.queued,
            model_used=settings.default_model,
        )
        db.add(job)
        jobs.append(BatchTailorJob(job_id=job.id, jd_id=jd.id))

    await db.commit()

    # ── Fire background task (parallel execution with semaphore) ──────
    background_tasks.add_task(run_batch_tailor, [j.job_id for j in jobs])

    return BatchTailorResponse(jobs=jobs, jd_count=len(apply_jds))
