"""
routers/jds.py

Single-JD read and update. The full session view (list of JDs) lives in
sessions.py — this router is for working with one JD directly.

Endpoints:
    GET    /api/jds/{id}  → full JD detail (all fields, richer than the list view)
    PATCH  /api/jds/{id}  → update user-editable fields; status patch auto-sets status_source=user

Not here yet (future sprints):
    POST   /api/jds/{id}/tailoring       → kick off single tailoring job
    GET    /api/jds/{id}/tailoring/{job_id} → tailoring status + outputs
"""

from datetime import datetime
from typing import Any, Optional
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
    User,
)
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
