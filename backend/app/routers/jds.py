"""
routers/jds.py

Single-JD read, update, and tailoring. The full session view (list of JDs)
lives in sessions.py — this router is for working with one JD directly.

Endpoints:
    GET    /api/jds/{id}                      → full JD detail
    PATCH  /api/jds/{id}                      → update user-editable fields
    GET    /api/jds/{id}/tailoring            → per-JD tailoring history (Sprint 6)
    POST   /api/jds/{id}/tailoring            → kick off single tailoring job (Sprint 5)
    GET    /api/jds/{id}/tailoring/{job_id}   → tailoring status + outputs (Sprint 5)
    GET    /api/jds/{id}/tailoring/{job_id}/docx → download generated resume docx (Sprint 5)
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.background import BackgroundTasks
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ..database import get_session
from ..models import (
    JD,
    JDStatus,
    JDStatusSource,
    Resume,
    Session as SessionModel,
    TailoringJob,
    TailoringStatus,
    User,
)
from ..services.tailoring import MAX_RESUMES, run_tailoring_job
from .sessions import get_current_user  # shared auth stub

router = APIRouter(prefix="/api/jds", tags=["jds"])


# ── Response schema ───────────────────────────────────────────────────────────
# Richer than sessions.JDRead (the list-view schema) — includes all enrichment
# fields the frontend needs when drilling into a single JD.

class JDDetail(BaseModel):
    id: UUID
    session_id: UUID
    number: int

    # Text
    raw_text: str
    cleaned_text: str

    # Metadata
    company: str
    role: str
    compensation: Optional[str]
    employee_count: Optional[str]
    link: Optional[str]

    # Status
    status: JDStatus
    status_source: JDStatusSource

    # Analysis
    analysis_text: Optional[str]
    requirements_met: Optional[Any]   # [{requirement, status, notes}]

    # Enrichment
    app_questions: Optional[str]
    additional_jd_text: Optional[str]
    cover_letter_requested: bool
    flagged_for_review: bool

    created_at: datetime

    model_config = {"from_attributes": True}


# ── Request schema ─────────────────────────────────────────────────────────────
# All fields optional — send only what you want to change.

class JDUpdate(BaseModel):
    status: Optional[JDStatus] = None
    company: Optional[str] = None
    role: Optional[str] = None
    compensation: Optional[str] = None
    link: Optional[str] = None
    app_questions: Optional[str] = None
    additional_jd_text: Optional[str] = None
    cover_letter_requested: Optional[bool] = None
    flagged_for_review: Optional[bool] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_jd_owned_by_user(
    jd_id: UUID,
    current_user: User,
    db: AsyncSession,
) -> JD:
    """
    Fetch a JD and verify it belongs to the current user (via session ownership).
    Raises 404 if not found or not owned.
    """
    jd = await db.get(JD, jd_id)
    if not jd:
        raise HTTPException(status_code=404, detail="JD not found")

    # Ownership: JD → Session → User
    session = await db.get(SessionModel, jd.session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="JD not found")

    return jd


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/{jd_id}", response_model=JDDetail)
async def get_jd(
    jd_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> JDDetail:
    """
    Full JD detail — all fields including analysis, enrichment, and raw text.
    The list view (GET /sessions/{id}) returns a leaner shape; use this when
    drilling into a single JD for review or tailoring.

    Errors:
        404  JD not found or doesn't belong to current user
    """
    jd = await _get_jd_owned_by_user(jd_id, current_user, db)
    return JDDetail.model_validate(jd)


@router.patch("/{jd_id}", response_model=JDDetail)
async def update_jd(
    jd_id: UUID,
    body: JDUpdate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> JDDetail:
    """
    Update user-editable fields on a JD. Send only what you want to change.

    Status rule: if `status` is included in the patch, `status_source` is
    automatically set to `user` — recording that a human overrode the AI verdict.

    Errors:
        404  JD not found or doesn't belong to current user
    """
    jd = await _get_jd_owned_by_user(jd_id, current_user, db)

    update_data = body.model_dump(exclude_unset=True)

    if "status" in update_data:
        jd.status = update_data["status"]
        jd.status_source = JDStatusSource.user  # always when human touches it

    # String fields — strip whitespace on the way in
    for field in ("company", "role", "compensation", "link", "app_questions", "additional_jd_text"):
        if field in update_data:
            val = update_data[field]
            setattr(jd, field, val.strip() if isinstance(val, str) else val)

    # Bool fields — set directly
    for field in ("cover_letter_requested", "flagged_for_review"):
        if field in update_data:
            setattr(jd, field, update_data[field])

    db.add(jd)
    await db.commit()
    await db.refresh(jd)

    return JDDetail.model_validate(jd)


# ── Tailoring schemas ─────────────────────────────────────────────────────────

class TailoringJobCreated(BaseModel):
    id: UUID
    jd_id: UUID
    status: TailoringStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class TailoringJobRead(BaseModel):
    id: UUID
    jd_id: UUID
    resume_id: UUID | None  # NULL after source resume deleted (ondelete SET NULL)
    status: TailoringStatus
    output_resume: Optional[str]
    output_cover_letter: Optional[str]
    output_app_answers: Optional[Any]       # [{question, answer}]
    has_docx: bool                          # True when output_resume_docx is populated
    model_used: str
    created_at: datetime
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}


# ── Tailoring endpoints ───────────────────────────────────────────────────────

@router.get("/{jd_id}/tailoring", response_model=list[TailoringJobRead])
async def list_tailoring_jobs(
    jd_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[TailoringJobRead]:
    """
    All tailoring jobs for a single JD, newest first.

    This is the per-JD tailoring history — shows every attempt, including
    superseded ones. Tab 4 prerequisite (Sprint 9).

    Errors:
        404  JD not found or doesn't belong to current user
    """
    jd = await _get_jd_owned_by_user(jd_id, current_user, db)

    result = await db.execute(
        select(TailoringJob)
        .where(TailoringJob.jd_id == jd.id)
        .order_by(TailoringJob.created_at.desc())
    )
    jobs = result.scalars().all()

    return [
        TailoringJobRead(
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
        )
        for job in jobs
    ]


@router.post(
    "/{jd_id}/tailoring",
    response_model=TailoringJobCreated,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_tailoring_job(
    jd_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TailoringJobCreated:
    """
    Kick off a tailoring job for a single JD.

    All of the user's resumes (up to 3) are sent to Claude — the prompt
    directs it to select the best source material. The most recent resume
    is stored as the FK reference on the job row.

    Returns 202 immediately. Poll GET /jds/{id}/tailoring/{job_id} for status.

    Errors:
        404  JD not found or doesn't belong to current user
        422  No resumes found, or more than 3 resumes (delete extras first)
    """
    jd = await _get_jd_owned_by_user(jd_id, current_user, db)

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

    # ── Create job row ────────────────────────────────────────────────
    from ..config import settings  # avoid circular at module level

    job = TailoringJob(
        jd_id=jd.id,
        resume_id=resumes[0].id,            # most recent as FK reference
        prompt_snapshot="",                  # filled by background task
        status=TailoringStatus.queued,
        model_used=settings.default_model,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # ── Fire background task ──────────────────────────────────────────
    background_tasks.add_task(run_tailoring_job, job.id)

    return TailoringJobCreated.model_validate(job)


@router.get("/{jd_id}/tailoring/{job_id}", response_model=TailoringJobRead)
async def get_tailoring_job(
    jd_id: UUID,
    job_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TailoringJobRead:
    """
    Poll tailoring job status and outputs.

    Frontend polls this after kicking off a job. Once status is "ready",
    all output fields are populated.

    Errors:
        404  JD or tailoring job not found, or doesn't belong to current user
    """
    jd = await _get_jd_owned_by_user(jd_id, current_user, db)

    job = await db.get(TailoringJob, job_id)
    if not job or job.jd_id != jd.id:
        raise HTTPException(status_code=404, detail="Tailoring job not found")

    return TailoringJobRead(
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
    )


@router.get("/{jd_id}/tailoring/{job_id}/docx")
async def download_tailoring_docx(
    jd_id: UUID,
    job_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Response:
    """
    Download the generated resume as a .docx file.

    Available once the tailoring job status is "ready" and has_docx is true.

    Errors:
        404  JD or job not found, or docx not yet generated
    """
    jd = await _get_jd_owned_by_user(jd_id, current_user, db)

    job = await db.get(TailoringJob, job_id)
    if not job or job.jd_id != jd.id:
        raise HTTPException(status_code=404, detail="Tailoring job not found")

    if not job.output_resume_docx:
        raise HTTPException(status_code=404, detail="Docx not yet generated")

    filename = f"{jd.company or 'resume'}_{jd.role or 'tailored'}.docx".replace(" ", "_")

    return Response(
        content=job.output_resume_docx,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
