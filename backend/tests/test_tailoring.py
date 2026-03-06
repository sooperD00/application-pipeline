"""
tests/test_tailoring.py

Integration tests for Sprint 5 — tailoring endpoints and prompt assembly.

Tests the endpoint wiring, DB state transitions, and prompt assembly logic.
Claude API is mocked — no real API calls.

Run with: pytest tests/test_tailoring.py -v
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.models import (
    JD,
    JDStatus,
    JDStatusSource,
    PromptPhase,
    PromptTemplate,
    Resume,
    Session as SessionModel,
    SessionStatus,
    TailoringJob,
    TailoringStatus,
)
from app.services.tailoring import assemble_tailoring_prompt


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
async def seeded_resume(db_session, seeded_user):
    """Create one resume for tailoring tests."""
    resume = Resume(
        user_id=seeded_user.id,
        label="Technical",
        content="Staff engineer with 13+ years building distributed systems.",
    )
    db_session.add(resume)
    await db_session.commit()
    await db_session.refresh(resume)
    return resume


@pytest.fixture
async def seeded_session_with_jds(db_session, seeded_user):
    """Create a session with 2 JDs (one apply, one pending)."""
    session = SessionModel(
        user_id=seeded_user.id,
        board="LinkedIn",
        filters="remote",
        search_term="data engineer",
        status=SessionStatus.complete,
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)

    jd_apply = JD(
        session_id=session.id,
        number=1,
        raw_text="We need a senior data engineer.",
        cleaned_text="We need a senior data engineer.",
        company="Acme Corp",
        role="Senior Data Engineer",
        status=JDStatus.apply,
        status_source=JDStatusSource.ai,
    )
    jd_pending = JD(
        session_id=session.id,
        number=2,
        raw_text="Junior role filler.",
        cleaned_text="Junior role filler.",
        company="Other Inc",
        role="Junior Dev",
        status=JDStatus.pending,
        status_source=JDStatusSource.ai,
    )
    db_session.add(jd_apply)
    db_session.add(jd_pending)
    await db_session.commit()
    await db_session.refresh(jd_apply)
    await db_session.refresh(jd_pending)

    return session, jd_apply, jd_pending


@pytest.fixture
async def seeded_templates(db_session):
    """Seed the 4 system-default prompt templates."""
    templates = []
    for phase, name in [
        (PromptPhase.analysis, "Analysis"),
        (PromptPhase.resume_generation, "Resume Generation"),
        (PromptPhase.cover_letter, "Cover Letter"),
        (PromptPhase.app_answers, "App Answers"),
    ]:
        t = PromptTemplate(
            user_id=None,
            phase=phase,
            name=name,
            template_text=f"Template for {{jd_text}} and {{resumes}} — phase: {phase.value}",
            version=1,
            is_active=True,
        )
        db_session.add(t)
        templates.append(t)

    await db_session.commit()
    for t in templates:
        await db_session.refresh(t)
    return templates


# ── POST /api/jds/{id}/tailoring ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_tailoring_job_returns_202(
    client, seeded_user, seeded_resume, seeded_session_with_jds, seeded_templates,
):
    _, jd_apply, _ = seeded_session_with_jds

    # Mock the background task — it creates its own DB session (AsyncSessionLocal)
    # which doesn't share the test's in-memory SQLite. We test the endpoint
    # response and job creation, not the background execution.
    with patch("app.routers.jds.run_tailoring_job", new_callable=AsyncMock):
        response = await client.post(f"/api/jds/{jd_apply.id}/tailoring")

    assert response.status_code == 202

    data = response.json()
    assert data["jd_id"] == str(jd_apply.id)
    assert data["status"] == "queued"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_tailoring_job_no_resumes_returns_422(
    client, seeded_user, seeded_session_with_jds,
):
    """Without any resumes, tailoring should fail with 422."""
    _, jd_apply, _ = seeded_session_with_jds

    response = await client.post(f"/api/jds/{jd_apply.id}/tailoring")
    assert response.status_code == 422
    assert "No resumes" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_tailoring_job_wrong_jd_returns_404(
    client, seeded_user, seeded_resume,
):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.post(f"/api/jds/{fake_id}/tailoring")
    assert response.status_code == 404


# ── GET /api/jds/{id}/tailoring/{job_id} ──────────────────────────────────────

@pytest.mark.asyncio
async def test_get_tailoring_job_queued(
    client, db_session, seeded_user, seeded_resume, seeded_session_with_jds,
):
    """A freshly created job should poll as queued."""
    _, jd_apply, _ = seeded_session_with_jds

    job = TailoringJob(
        jd_id=jd_apply.id,
        resume_id=seeded_resume.id,
        prompt_snapshot="test prompt",
        status=TailoringStatus.queued,
        model_used="claude-opus-4-6",
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    response = await client.get(f"/api/jds/{jd_apply.id}/tailoring/{job.id}")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "queued"
    assert data["output_resume"] is None
    assert data["has_docx"] is False


@pytest.mark.asyncio
async def test_get_tailoring_job_ready_with_outputs(
    client, db_session, seeded_user, seeded_resume, seeded_session_with_jds,
):
    """A completed job should return all outputs and has_docx=True."""
    _, jd_apply, _ = seeded_session_with_jds

    job = TailoringJob(
        jd_id=jd_apply.id,
        resume_id=seeded_resume.id,
        prompt_snapshot="test prompt",
        status=TailoringStatus.ready,
        model_used="claude-opus-4-6",
        output_resume="NICOLE L. ROWSEY\nStaff-level engineer...",
        output_cover_letter="Dear Hiring Manager...",
        output_app_answers=[{"question": "Why us?", "answer": "Mission alignment."}],
        output_resume_docx=b"fake-docx-bytes",
        completed_at=datetime.utcnow(),
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    response = await client.get(f"/api/jds/{jd_apply.id}/tailoring/{job.id}")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ready"
    assert data["output_resume"] is not None
    assert data["output_cover_letter"] is not None
    assert data["has_docx"] is True
    assert len(data["output_app_answers"]) == 1


@pytest.mark.asyncio
async def test_get_tailoring_job_wrong_job_id_returns_404(
    client, seeded_user, seeded_resume, seeded_session_with_jds,
):
    _, jd_apply, _ = seeded_session_with_jds
    fake_id = "00000000-0000-0000-0000-000000000000"

    response = await client.get(f"/api/jds/{jd_apply.id}/tailoring/{fake_id}")
    assert response.status_code == 404


# ── GET /api/jds/{id}/tailoring/{job_id}/docx ─────────────────────────────────

@pytest.mark.asyncio
async def test_download_docx_returns_bytes(
    client, db_session, seeded_user, seeded_resume, seeded_session_with_jds,
):
    _, jd_apply, _ = seeded_session_with_jds

    job = TailoringJob(
        jd_id=jd_apply.id,
        resume_id=seeded_resume.id,
        prompt_snapshot="test",
        status=TailoringStatus.ready,
        model_used="claude-opus-4-6",
        output_resume_docx=b"PK\x03\x04fake-docx-content",
        completed_at=datetime.utcnow(),
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    response = await client.get(f"/api/jds/{jd_apply.id}/tailoring/{job.id}/docx")
    assert response.status_code == 200
    assert "application/vnd.openxmlformats" in response.headers["content-type"]
    assert b"PK" in response.content  # docx files start with PK (zip header)


@pytest.mark.asyncio
async def test_download_docx_not_ready_returns_404(
    client, db_session, seeded_user, seeded_resume, seeded_session_with_jds,
):
    _, jd_apply, _ = seeded_session_with_jds

    job = TailoringJob(
        jd_id=jd_apply.id,
        resume_id=seeded_resume.id,
        prompt_snapshot="test",
        status=TailoringStatus.queued,
        model_used="claude-opus-4-6",
        # no output_resume_docx
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    response = await client.get(f"/api/jds/{jd_apply.id}/tailoring/{job.id}/docx")
    assert response.status_code == 404


# ── POST /api/sessions/{id}/batch-tailor ──────────────────────────────────────

@pytest.mark.asyncio
async def test_batch_tailor_creates_jobs_for_apply_jds(
    client, seeded_user, seeded_resume, seeded_session_with_jds, seeded_templates,
):
    """Batch tailor should create jobs only for apply-status JDs."""
    session, jd_apply, jd_pending = seeded_session_with_jds

    # Mock the background task — same reason as single tailoring test
    with patch("app.routers.sessions.run_batch_tailor", new_callable=AsyncMock):
        response = await client.post(f"/api/sessions/{session.id}/batch-tailor")

    assert response.status_code == 202

    data = response.json()
    assert data["jd_count"] == 1  # only the apply JD
    assert len(data["jobs"]) == 1
    assert "job_id" in data["jobs"][0]
    assert "jd_id" in data["jobs"][0]


@pytest.mark.asyncio
async def test_batch_tailor_no_resumes_returns_422(
    client, seeded_user, seeded_session_with_jds,
):
    session, _, _ = seeded_session_with_jds

    response = await client.post(f"/api/sessions/{session.id}/batch-tailor")
    assert response.status_code == 422
    assert "No resumes" in response.json()["detail"]


@pytest.mark.asyncio
async def test_batch_tailor_no_apply_jds_returns_422(
    client, db_session, seeded_user, seeded_resume,
):
    """Session with only pending JDs should fail."""
    session = SessionModel(
        user_id=seeded_user.id,
        board="LinkedIn",
        filters="remote",
        search_term="test",
        status=SessionStatus.complete,
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)

    jd = JD(
        session_id=session.id,
        number=1,
        raw_text="Some JD text here.",
        cleaned_text="Some JD text here.",
        company="Test Co",
        role="Test Role",
        status=JDStatus.pending,
        status_source=JDStatusSource.ai,
    )
    db_session.add(jd)
    await db_session.commit()

    response = await client.post(f"/api/sessions/{session.id}/batch-tailor")
    assert response.status_code == 422
    assert "apply" in response.json()["detail"].lower()


# ── Prompt assembly unit tests ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_prompt_assembly_includes_analysis_and_resume_generation():
    """Required templates should always be concatenated."""
    jd = JD(
        id=uuid4(), session_id=uuid4(), number=1,
        raw_text="test", cleaned_text="We need a data engineer.",
        company="Acme", role="Data Engineer",
        status=JDStatus.apply, status_source=JDStatusSource.ai,
    )
    resumes = [Resume(id=uuid4(), user_id=uuid4(), label="Tech", content="My resume text.")]

    templates = {
        PromptPhase.analysis: PromptTemplate(
            id=uuid4(), phase=PromptPhase.analysis, name="a",
            template_text="Analyze: {jd_text} against {resumes}",
            version=1, is_active=True,
        ),
        PromptPhase.resume_generation: PromptTemplate(
            id=uuid4(), phase=PromptPhase.resume_generation, name="r",
            template_text="Tailor for {company} - {role}",
            version=1, is_active=True,
        ),
    }

    result = assemble_tailoring_prompt(jd, resumes, templates)

    assert "We need a data engineer." in result  # {jd_text} substituted
    assert "My resume text." in result            # {resumes} substituted
    assert "Acme" in result                       # {company} substituted
    assert "Data Engineer" in result              # {role} substituted


@pytest.mark.asyncio
async def test_prompt_assembly_conditional_cover_letter():
    """Cover letter template should only appear when cover_letter_requested."""
    jd_no_cl = JD(
        id=uuid4(), session_id=uuid4(), number=1,
        raw_text="t", cleaned_text="JD text",
        company="A", role="R",
        cover_letter_requested=False,
        status=JDStatus.apply, status_source=JDStatusSource.ai,
    )
    jd_with_cl = JD(
        id=uuid4(), session_id=uuid4(), number=1,
        raw_text="t", cleaned_text="JD text",
        company="A", role="R",
        cover_letter_requested=True,
        status=JDStatus.apply, status_source=JDStatusSource.ai,
    )
    resumes = [Resume(id=uuid4(), user_id=uuid4(), label="T", content="resume")]

    templates = {
        PromptPhase.analysis: PromptTemplate(
            id=uuid4(), phase=PromptPhase.analysis, name="a",
            template_text="analyze", version=1, is_active=True,
        ),
        PromptPhase.resume_generation: PromptTemplate(
            id=uuid4(), phase=PromptPhase.resume_generation, name="r",
            template_text="tailor", version=1, is_active=True,
        ),
        PromptPhase.cover_letter: PromptTemplate(
            id=uuid4(), phase=PromptPhase.cover_letter, name="cl",
            template_text="COVER_LETTER_MARKER", version=1, is_active=True,
        ),
    }

    result_without = assemble_tailoring_prompt(jd_no_cl, resumes, templates)
    result_with = assemble_tailoring_prompt(jd_with_cl, resumes, templates)

    assert "COVER_LETTER_MARKER" not in result_without
    assert "COVER_LETTER_MARKER" in result_with


@pytest.mark.asyncio
async def test_prompt_assembly_conditional_app_answers():
    """App answers template should only appear when app_questions is populated."""
    jd_no_q = JD(
        id=uuid4(), session_id=uuid4(), number=1,
        raw_text="t", cleaned_text="JD text",
        company="A", role="R",
        app_questions=None,
        status=JDStatus.apply, status_source=JDStatusSource.ai,
    )
    jd_with_q = JD(
        id=uuid4(), session_id=uuid4(), number=1,
        raw_text="t", cleaned_text="JD text",
        company="A", role="R",
        app_questions="* Why do you want this role?",
        status=JDStatus.apply, status_source=JDStatusSource.ai,
    )
    resumes = [Resume(id=uuid4(), user_id=uuid4(), label="T", content="resume")]

    templates = {
        PromptPhase.analysis: PromptTemplate(
            id=uuid4(), phase=PromptPhase.analysis, name="a",
            template_text="analyze", version=1, is_active=True,
        ),
        PromptPhase.resume_generation: PromptTemplate(
            id=uuid4(), phase=PromptPhase.resume_generation, name="r",
            template_text="tailor", version=1, is_active=True,
        ),
        PromptPhase.app_answers: PromptTemplate(
            id=uuid4(), phase=PromptPhase.app_answers, name="aq",
            template_text="APP_ANSWERS_MARKER for {app_questions}",
            version=1, is_active=True,
        ),
    }

    result_without = assemble_tailoring_prompt(jd_no_q, resumes, templates)
    result_with = assemble_tailoring_prompt(jd_with_q, resumes, templates)

    assert "APP_ANSWERS_MARKER" not in result_without
    assert "APP_ANSWERS_MARKER" in result_with
    assert "Why do you want this role?" in result_with
