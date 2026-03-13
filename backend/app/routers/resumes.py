"""
routers/resumes.py

Resume CRUD. Users paste and label resume versions here; Claude sees
the text for analysis and tailoring. Binary upload (docx/pdf) is Phase N.

Endpoints:
    POST   /api/resumes       → create (max 3 per user)
    GET    /api/resumes        → list all resumes for current user
    PATCH  /api/resumes/{id}  → edit label and/or content
    DELETE /api/resumes/{id}  → delete

Constraint: max 3 resumes per user, enforced at API layer (not DB).
See service-layer-notes.md for the count-check-before-insert pattern.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ..database import get_session
from ..models import Resume, User
from .sessions import get_current_user  # shared auth stub

MAX_RESUMES_PER_USER = 3

router = APIRouter(prefix="/api/resumes", tags=["resumes"])


# ── Request schemas ───────────────────────────────────────────────────────────

class ResumeCreate(BaseModel):
    label: str          # e.g. "Technical", "Leadership"
    content: str        # pasted resume text


class ResumeUpdate(BaseModel):
    label: str | None = None
    content: str | None = None


# ── Response schema ───────────────────────────────────────────────────────────

class ResumeRead(BaseModel):
    id: UUID
    user_id: UUID
    label: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("", response_model=ResumeRead, status_code=status.HTTP_201_CREATED)
async def create_resume(
    body: ResumeCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ResumeRead:
    """
    Paste a resume and give it a label. Max 3 per user.

    Errors:
        409  already at 3 resumes — delete one first
        422  validation error (empty label or content)
    """
    # ── 3-resume cap ──────────────────────────────────────────────────────────
    result = await db.execute(select(Resume).where(Resume.user_id == current_user.id))
    existing = result.scalars().all()
    if len(existing) >= MAX_RESUMES_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"You already have {MAX_RESUMES_PER_USER} resumes. Delete one before adding another.",
        )

    label = body.label.strip()
    content = body.content.strip()

    if not label:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="label cannot be empty",
        )
    if not content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="content cannot be empty",
        )

    resume = Resume(user_id=current_user.id, label=label, content=content)
    db.add(resume)
    await db.commit()
    await db.refresh(resume)

    return ResumeRead.model_validate(resume)


@router.get("", response_model=list[ResumeRead])
async def list_resumes(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[ResumeRead]:
    """
    All resumes for the current user, ordered by creation date (oldest first).
    Typical response: 1–3 items.
    """
    result = await db.execute(
        select(Resume)
        .where(Resume.user_id == current_user.id)
        .order_by(Resume.created_at)
    )
    resumes = result.scalars().all()
    return [ResumeRead.model_validate(r) for r in resumes]


@router.patch("/{resume_id}", response_model=ResumeRead)
async def update_resume(
    resume_id: UUID,
    body: ResumeUpdate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ResumeRead:
    """
    Edit a resume's label, content, or both. Omit a field to leave it unchanged.

    Errors:
        404  resume not found or doesn't belong to current user
        422  update would leave label or content empty
    """
    resume = await db.get(Resume, resume_id)
    if not resume or resume.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Resume not found")

    if body.label is not None:
        label = body.label.strip()
        if not label:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="label cannot be empty",
            )
        resume.label = label

    if body.content is not None:
        content = body.content.strip()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="content cannot be empty",
            )
        resume.content = content

    db.add(resume)
    await db.commit()
    await db.refresh(resume)

    return ResumeRead.model_validate(resume)


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete a resume. Frees up a slot (cap is 3).

    TailoringJobs that referenced this resume keep their outputs intact —
    the FK has ondelete=SET NULL so resume_id becomes NULL, but
    prompt_snapshot, output_resume, and output_resume_docx are
    self-contained. See ADR-017 for the snapshot design direction.

    Errors:
        404  resume not found or doesn't belong to current user
    """
    resume = await db.get(Resume, resume_id)
    if not resume or resume.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Resume not found")

    await db.delete(resume)
    await db.commit()
