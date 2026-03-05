"""
services/analysis.py

Batch JD analysis via Claude. Called from POST /sessions/{id}/analyze.

Yields raw SSE-formatted strings — the endpoint wraps these in StreamingResponse.

Event sequence per session:
    batch_start      → {"batch": 1, "jd_numbers": [1,2,3,4,5]}
    jd_result        → {"jd_id": "...", "number": 1, "status": "apply", "analysis": "...",
                        "requirements_met": [...], "exclude_company": false}
    ...              → (one jd_result per JD in batch)
    batch_complete   → {"batch": 1, "meta_analysis": "Cross-JD observations..."}
    batch_start      → {"batch": 2, "jd_numbers": [6,7,8,9,10]}
    ...
    analysis_complete → {"session_id": "...", "summary": {"apply": 6, "maybe": 3, "no": 16}}

On error (after one retry):
    error            → {"batch": N, "message": "...", "recoverable": true}
    (session status reset to active so user can re-trigger)

The conversation context threads across all batches. Claude sees earlier JDs when
writing each meta-analysis, enabling cross-session strategic observations.
"""

import asyncio
import json
import re
from collections.abc import AsyncGenerator
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ..models import (
    JD,
    JDStatus,
    JDStatusSource,
    Resume,
    Session as SessionModel,
    SessionStatus,
    User,
)
from .claude import ClaudeConversation


# ── Analysis system prompt ────────────────────────────────────────────────────
#
# Modeled closely on Nicole's manual workflow prompt #1. Key design choices:
#   - Explicit JSON-only instruction (no preamble, no markdown fences)
#   - Asks Claude to distinguish "deep expertise" language from "exposure to"
#   - Cross-JD meta-analysis after every batch (the strategic advice layer)
#   - exclude_company flag for crypto/recruiter/staffing firms
#
# TODO: move this to PromptTemplate table (phase = PromptPhase.analysis)
#       so it's user-editable without a redeploy.

ANALYSIS_SYSTEM_PROMPT = """\
You are analyzing job descriptions for a senior data/software engineer candidate.

You will receive the candidate's resumes (1–3 versions, each labeled) and then \
batches of job descriptions — up to 5 at a time, each prefaced with its session number.

For each JD, analyze carefully:
- Count required qualifications the candidate genuinely has production experience in \
vs. ones they would be learning on the job.
- Pay close attention to language: "deep expertise" / "advanced" / "5+ years" signals \
a hard requirement. "Familiar with" / "exposure to" / "nice to have" signals a stretch \
that's worth attempting. A stretch role is different from a clear mismatch.
- Assess whether gaps are central to the role or peripheral to it.
- Identify if the company appears to be crypto/blockchain, a recruiter, or a staffing firm.

Categorize each JD as apply / maybe / no with your full reasoning.

After each batch, write a meta_analysis: cross-JD strategic observations, skill gap \
patterns you're noticing, whether the candidate should scrape more JDs or start \
applying from what they have, and a list of company names suitable for a LinkedIn \
exclusion filter (crypto/recruiters), formatted as: Company1 OR Company2.

IMPORTANT: Respond ONLY with a single JSON object. No preamble. No markdown fences. \
No text outside the JSON. Use this exact structure:

{
  "results": [
    {
      "jd_number": <int>,
      "status": "apply" | "maybe" | "no",
      "analysis": "<your full reasoning for this JD>",
      "requirements_met": [
        {
          "requirement": "<specific skill or qualification from the JD>",
          "status": "yes" | "partial" | "no",
          "notes": "<brief supporting note>"
        }
      ],
      "exclude_company": <bool>
    }
  ],
  "meta_analysis": "<cross-JD observations, apply-now vs scrape-more advice, \
and LinkedIn exclusion filter formatted as: Company1 OR Company2>"
}

Take your time. Accuracy over speed.
"""


# ── SSE helpers ───────────────────────────────────────────────────────────────

def _sse(event: str, data: dict) -> str:
    """Format a named SSE event as a raw string ready to stream."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _parse_claude_json(text: str) -> dict:
    """
    Parse Claude's JSON response, tolerating accidental markdown fences.
    Raises json.JSONDecodeError if the result still can't be parsed — let
    the caller handle that as a batch-level error.
    """
    s = text.strip()
    # Strip ```json...``` or ```...``` wrapping (Claude sometimes ignores the instruction)
    s = re.sub(r"^```(?:json)?\s*\n?", "", s)
    s = re.sub(r"\n?```\s*$", "", s)
    return json.loads(s.strip())


async def _send_with_retry(
    conversation: ClaudeConversation,
    message: str,
    retries: int = 1,
) -> tuple[str, int]:
    """
    Send a message, retrying up to `retries` times on any exception.
    Waits 3 seconds between attempts (covers transient 529s and timeouts).
    Raises the last exception if all attempts are exhausted.
    """
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return await conversation.send(message)
        except Exception as exc:
            last_exc = exc
            if attempt < retries:
                await asyncio.sleep(3)
    raise last_exc  # type: ignore[misc]


# ── Prompt assembly ───────────────────────────────────────────────────────────

def _resume_block(resumes: list[Resume]) -> str:
    """Format all of the user's resumes into the first-batch message."""
    parts = []
    for r in resumes:
        parts.append(
            f"--- Resume: {r.label} ---\n{r.content}\n--- End Resume: {r.label} ---"
        )
    return "\n\n".join(parts)


def _jd_block(jds: list[JD]) -> str:
    """Format a batch of JDs into the user message body."""
    parts = []
    for jd in jds:
        company = jd.company or "Unknown Company"
        role = jd.role or "Unknown Role"
        header = f"JD #{jd.number}: {company} — {role}"
        parts.append(
            f"--- {header} ---\n{jd.cleaned_text}\n--- End JD #{jd.number} ---"
        )
    return "\n\n".join(parts)


# ── Main generator ────────────────────────────────────────────────────────────

async def stream_analysis(
    session_id: UUID,
    db: AsyncSession,
    user: User,
) -> AsyncGenerator[str, None]:
    """
    Core analysis generator. Fetches session + JDs + resumes, batches JDs into
    groups of 5, threads conversation context across all batches, writes results
    to DB as they arrive, and yields SSE-formatted strings throughout.

    The endpoint wraps this in StreamingResponse. Caller validates that the
    session exists and isn't already analyzing before calling this.
    """
    # ── Load data ─────────────────────────────────────────────────────────────
    session = await db.get(SessionModel, session_id)
    if not session or session.user_id != user.id:
        yield _sse("error", {"message": "Session not found", "recoverable": False})
        return

    jd_result = await db.execute(
        select(JD).where(JD.session_id == session_id).order_by(JD.number)
    )
    jds = jd_result.scalars().all()

    if not jds:
        yield _sse("error", {"message": "No JDs to analyze", "recoverable": False})
        return

    resume_result = await db.execute(
        select(Resume)
        .where(Resume.user_id == user.id)
        .order_by(Resume.created_at.desc())
    )
    resumes = resume_result.scalars().all()

    if not resumes:
        yield _sse("error", {
            "message": "No resume found. Paste at least one resume before analyzing.",
            "recoverable": False,
        })
        return

    # ── Mark session as in-progress ───────────────────────────────────────────
    session.status = SessionStatus.analyzing
    db.add(session)
    await db.commit()

    # ── Set up conversation ───────────────────────────────────────────────────
    conversation = ClaudeConversation(system=ANALYSIS_SYSTEM_PROMPT)

    # ── Batch loop ────────────────────────────────────────────────────────────
    batch_size = 5
    batches = [jds[i : i + batch_size] for i in range(0, len(jds), batch_size)]
    counts: dict[str, int] = {"apply": 0, "maybe": 0, "no": 0}

    for batch_index, batch in enumerate(batches):
        batch_num = batch_index + 1
        jd_numbers = [jd.number for jd in batch]

        yield _sse("batch_start", {"batch": batch_num, "jd_numbers": jd_numbers})

        # Build the user turn — first batch includes resumes, subsequent ones don't
        jd_text = _jd_block(list(batch))
        if batch_index == 0:
            resume_text = _resume_block(list(resumes))
            message = (
                f"Here are the candidate's resumes:\n\n{resume_text}\n\n"
                f"Please analyze the following {len(batch)} job description(s):\n\n{jd_text}"
            )
        else:
            message = (
                f"Please scrutinize these {len(batch)} job description(s) "
                f"in the same manner:\n\n{jd_text}"
            )

        # ── Call Claude (one retry on failure) ────────────────────────────────
        try:
            raw_response, _tokens = await _send_with_retry(conversation, message)
        except Exception as exc:
            # Reset session so the user can re-trigger analyze
            session.status = SessionStatus.active
            db.add(session)
            await db.commit()
            yield _sse("error", {
                "batch": batch_num,
                "message": f"Claude API error after retry: {exc}",
                "recoverable": True,
            })
            return

        # ── Parse response ────────────────────────────────────────────────────
        try:
            parsed = _parse_claude_json(raw_response)
        except json.JSONDecodeError:
            session.status = SessionStatus.active
            db.add(session)
            await db.commit()
            yield _sse("error", {
                "batch": batch_num,
                "message": "Claude returned unparseable JSON. Re-run analysis to retry.",
                "recoverable": True,
            })
            return

        # ── Write JD results to DB and stream events ──────────────────────────
        # Index the batch by number — Claude might return results out of order
        jd_by_number = {jd.number: jd for jd in batch}

        for item in parsed.get("results", []):
            jd_number = item.get("jd_number")
            jd = jd_by_number.get(jd_number)
            if jd is None:
                continue  # Claude returned a number we didn't send — skip it

            raw_status = str(item.get("status", "maybe")).lower()
            status_val = (
                JDStatus(raw_status)
                if raw_status in ("apply", "maybe", "no")
                else JDStatus.maybe
            )

            jd.status = status_val
            jd.status_source = JDStatusSource.ai
            jd.analysis_text = item.get("analysis", "")
            jd.requirements_met = item.get("requirements_met", [])
            db.add(jd)

            counts[status_val.value] += 1

            yield _sse("jd_result", {
                "jd_id": str(jd.id),
                "number": jd.number,
                "status": status_val.value,
                "analysis": jd.analysis_text,
                "requirements_met": jd.requirements_met,
                "exclude_company": item.get("exclude_company", False),
            })

        # ── Commit the batch and update rolling meta-analysis ─────────────────
        # All JD updates + meta-analysis write commit together — atomic per batch
        meta = parsed.get("meta_analysis", "")
        session.meta_analysis = meta
        db.add(session)
        await db.commit()

        yield _sse("batch_complete", {"batch": batch_num, "meta_analysis": meta})

    # ── All batches complete ──────────────────────────────────────────────────
    session.status = SessionStatus.complete
    db.add(session)
    await db.commit()

    yield _sse("analysis_complete", {
        "session_id": str(session_id),
        "summary": counts,
    })
