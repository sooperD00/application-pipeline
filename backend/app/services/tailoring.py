"""
services/tailoring.py

Tailoring job orchestration — prompt assembly, Claude API call, response
parsing, and docx generation.

ARCHITECTURE (ADR-011, ADR-012):
    - Prompt templates live in the DB (PromptTemplate table), editable per user
    - Templates control ALL formatting decisions — the code is a dumb executor
    - Claude returns structured JSON; docx_builder.py renders it into .docx
    - prompt_snapshot on TailoringJob freezes the exact prompt used

COMPOSABLE TEMPLATES assembled into one Claude call:
    1. analysis          — always included (fit assessment for this specific JD)
    2. resume_generation — always included (tailored resume as structured JSON)
    3. cover_letter      — included only if jd.cover_letter_requested
    4. app_answers       — included only if jd.app_questions is populated

All of the user's resumes (up to 3) are sent to Claude in the prompt.
Claude selects the best source material. Hard cap enforced at API layer.

EXECUTION MODEL:
    Single job:  BackgroundTasks kicks off run_tailoring_job()
    Batch:       One BackgroundTask runs run_batch_tailor() which wraps
                 asyncio.gather + Semaphore(settings.tailoring_parallelism)
    Both create their own DB sessions (background tasks outlive the request).
"""

import asyncio
import json
import logging
import re
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ..config import settings
from ..database import AsyncSessionLocal
from ..models import (
    JD,
    PromptPhase,
    PromptTemplate,
    Resume,
    Session as SessionModel,
    TailoringJob,
    TailoringStatus
)
from .claude import ClaudeConversation
from .docx_builder import build_resume_docx

logger = logging.getLogger(__name__)

# Hard cap on resumes per tailoring call. If the user has more than this,
# the endpoint returns 422 before creating the job. This matches the
# API-layer max of 3 enforced in resumes.py.
MAX_RESUMES = 3


# ── System prompt (generic wrapper — template content drives the real work) ───

TAILORING_SYSTEM_PROMPT = """\
You are a career document specialist. You will receive instructions for \
analyzing a job description, tailoring a resume, and optionally writing a \
cover letter and/or answering application questions.

CRITICAL: Respond ONLY with a single JSON object. No preamble. No markdown \
fences. No text outside the JSON.

The required fields are specified in the instructions you receive. At minimum \
your response must include:
{
  "analysis": "<your fit analysis and reasoning>",
  "strategy": "<your tailoring strategy>",
  "resume": {
    "elements": [<array of formatted elements — schema in instructions>]
  }
}

Optional fields (include ONLY when the instructions request them):
  "cover_letter": "<plain text with paragraph breaks>"
  "app_answers": [{"question": "...", "answer": "..."}]

Take your time. Quality and accuracy over speed.\
"""


# ── JSON parsing (shared with analysis.py) ────────────────────────────────────

def _parse_claude_json(text: str) -> dict:
    """Parse Claude's JSON response, tolerating accidental markdown fences."""
    s = text.strip()
    s = re.sub(r"^```(?:json)?\s*\n?", "", s)
    s = re.sub(r"\n?```\s*$", "", s)
    return json.loads(s.strip())


# ── Template fetching ─────────────────────────────────────────────────────────

async def _get_active_templates(
    db: AsyncSession,
    user_id: UUID,
    phases: list[PromptPhase],
) -> dict[PromptPhase, PromptTemplate]:
    """
    Fetch the active PromptTemplate for each requested phase.
    User-specific templates take priority over system defaults (user_id IS NULL).
    Returns a dict mapping phase → template. Missing phases are omitted.
    """
    templates: dict[PromptPhase, PromptTemplate] = {}

    for phase in phases:
        # User-specific first
        result = await db.execute(
            select(PromptTemplate)
            .where(
                PromptTemplate.phase == phase,
                PromptTemplate.is_active == True,  # noqa: E712
                PromptTemplate.user_id == user_id,
            )
            .order_by(PromptTemplate.version.desc())
            .limit(1)
        )
        template = result.scalars().first()

        if not template:
            # System default fallback
            result = await db.execute(
                select(PromptTemplate)
                .where(
                    PromptTemplate.phase == phase,
                    PromptTemplate.is_active == True,  # noqa: E712
                    PromptTemplate.user_id == None,  # noqa: E711
                )
                .order_by(PromptTemplate.version.desc())
                .limit(1)
            )
            template = result.scalars().first()

        if template:
            templates[phase] = template

    return templates


# ── Prompt assembly ───────────────────────────────────────────────────────────

def _format_resumes(resumes: list[Resume]) -> str:
    """Format all of the user's resumes into the prompt."""
    parts = []
    for r in resumes:
        parts.append(
            f"--- Resume: {r.label} ---\n{r.content}\n--- End Resume: {r.label} ---"
        )
    return "\n\n".join(parts)


def assemble_tailoring_prompt(
    jd: JD,
    resumes: list[Resume],
    templates: dict[PromptPhase, PromptTemplate],
) -> str:
    """
    Assemble the tailoring prompt from composable templates.

    Substitutes variables ({jd_text}, {resumes}, {company}, etc.) and
    concatenates templates in order:
        analysis → resume_generation → [cover_letter] → [app_answers]

    The assembled text becomes the user message to Claude. It's also stored
    as prompt_snapshot on the TailoringJob, frozen at kick-off time.
    """
    variables = {
        "jd_text": jd.cleaned_text,
        "resumes": _format_resumes(resumes),
        "company": jd.company or "Unknown Company",
        "role": jd.role or "Unknown Role",
        "compensation": jd.compensation or "Not specified",
        "app_questions": jd.app_questions or "",
    }

    sections = []

    # Required templates
    for phase in [PromptPhase.analysis, PromptPhase.resume_generation]:
        if phase in templates:
            text = templates[phase].template_text
            for key, val in variables.items():
                text = text.replace(f"{{{key}}}", val)
            sections.append(text)

    # Conditional: cover_letter
    if jd.cover_letter_requested and PromptPhase.cover_letter in templates:
        text = templates[PromptPhase.cover_letter].template_text
        for key, val in variables.items():
            text = text.replace(f"{{{key}}}", val)
        sections.append(text)

    # Conditional: app_answers
    if jd.app_questions and PromptPhase.app_answers in templates:
        text = templates[PromptPhase.app_answers].template_text
        for key, val in variables.items():
            text = text.replace(f"{{{key}}}", val)
        sections.append(text)

    return "\n\n---\n\n".join(sections)


# ── Text extraction from structured elements ──────────────────────────────────

def _extract_text_from_elements(elements: list[dict]) -> str:
    """
    Build a plain-text representation of the resume from structured elements.
    Stored as TailoringJob.output_resume for in-app display and comparison.
    This is extracted FROM the structured output, not an input TO the docx.
    """
    lines = []
    for el in elements:
        el_type = el.get("type", "")
        text = el.get("text", "")

        if el_type == "blank_line":
            lines.append("")
        elif el_type == "section_header":
            lines.append(f"\n{text}")
            lines.append("-" * len(text))
        elif el_type == "bullet":
            lines.append(f"  \u2022 {text}")
        elif text:
            lines.append(text)

    return "\n".join(lines)


# ── Single job execution ──────────────────────────────────────────────────────

async def run_tailoring_job(job_id: UUID) -> None:
    """
    Execute a single tailoring job. Creates its own DB session
    (background tasks outlive the request that spawned them).

    Lifecycle: queued → processing → ready
    On error: sets status to failed and returns. The polling UI shows
    the failure and offers a retry button.
    """
    async with AsyncSessionLocal() as db:
        # ── Load the job ──────────────────────────────────────────────
        job = await db.get(TailoringJob, job_id)
        if not job:
            logger.error("TailoringJob %s not found", job_id)
            return  # no job row to mark failed

        job.status = TailoringStatus.processing
        db.add(job)
        await db.commit()

        # ── Load related data ─────────────────────────────────────────
        jd = await db.get(JD, job.jd_id)
        if not jd:
            logger.error("JD %s not found for job %s", job.jd_id, job_id)
            job.status = TailoringStatus.failed
            db.add(job)
            await db.commit()
            return

        session_model = await db.get(SessionModel, jd.session_id)
        if not session_model:
            job.status = TailoringStatus.failed
            db.add(job)
            await db.commit()
            return

        user_id = session_model.user_id

        # All resumes go to Claude (hard cap already enforced at endpoint)
        result = await db.execute(
            select(Resume)
            .where(Resume.user_id == user_id)
            .order_by(Resume.created_at.desc())
        )
        resumes = list(result.scalars().all())

        if not resumes:
            logger.error("No resumes for user %s, job %s", user_id, job_id)
            job.status = TailoringStatus.failed
            db.add(job)
            await db.commit()
            return

        # ── Fetch active templates ────────────────────────────────────
        phases = [PromptPhase.analysis, PromptPhase.resume_generation]
        if jd.cover_letter_requested:
            phases.append(PromptPhase.cover_letter)
        if jd.app_questions:
            phases.append(PromptPhase.app_answers)

        templates = await _get_active_templates(db, user_id, phases)

        if PromptPhase.resume_generation not in templates:
            logger.error("No resume_generation template found for job %s", job_id)
            job.status = TailoringStatus.failed
            db.add(job)
            await db.commit()
            return

        # ── Assemble prompt and snapshot it ────────────────────────────
        assembled = assemble_tailoring_prompt(jd, resumes, templates)
        job.prompt_snapshot = assembled

        # ── Call Claude ───────────────────────────────────────────────
        try:
            conversation = ClaudeConversation(
                system=TAILORING_SYSTEM_PROMPT,
                model=job.model_used,
                max_tokens=16384,
            )
            raw_response, _tokens = await conversation.send(assembled)
        except Exception as exc:
            logger.exception("Claude API error for job %s: %s", job_id, exc)
            job.status = TailoringStatus.failed
            db.add(job)
            await db.commit()
            return

        # ── Parse structured response ─────────────────────────────────
        try:
            parsed = _parse_claude_json(raw_response)
        except json.JSONDecodeError as exc:
            logger.error("Unparseable JSON from Claude for job %s: %s", job_id, exc)
            job.status = TailoringStatus.failed
            db.add(job)
            await db.commit()
            return

        # ── Generate docx ─────────────────────────────────────────────
        resume_elements = parsed.get("resume", {}).get("elements", [])

        if resume_elements:
            try:
                job.output_resume_docx = build_resume_docx(resume_elements)
                job.output_resume = _extract_text_from_elements(resume_elements)
            except Exception as exc:
                logger.exception("Docx generation failed for job %s: %s", job_id, exc)
                # Still save what we can — text extraction might work
                job.output_resume = _extract_text_from_elements(resume_elements)

        # ── Save remaining outputs ────────────────────────────────────
        job.output_cover_letter = parsed.get("cover_letter")
        app_answers = parsed.get("app_answers")
        if app_answers:
            job.output_app_answers = app_answers

        job.chat_context = conversation.history
        job.status = TailoringStatus.ready
        job.completed_at = datetime.utcnow()

        db.add(job)
        await db.commit()

        logger.info("TailoringJob %s completed (JD: %s)", job_id, jd.company)


# ── Batch execution ───────────────────────────────────────────────────────────

async def run_batch_tailor(job_ids: list[UUID]) -> None:
    """
    Run multiple tailoring jobs in parallel, capped by semaphore.
    Called as a single BackgroundTask from the batch-tailor endpoint.

    ADR-008: free tier = 4 parallel, paid tier = 8 (just change
    settings.tailoring_parallelism).
    """
    semaphore = asyncio.Semaphore(settings.tailoring_parallelism)

    async def _run_one(job_id: UUID) -> None:
        async with semaphore:
            await run_tailoring_job(job_id)

    await asyncio.gather(*[_run_one(jid) for jid in job_ids])
