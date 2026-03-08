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


# ══════════════════════════════════════════════════════════════════════════════
# Sprint 6 — New endpoints, skip logic, pipeline integration
# ══════════════════════════════════════════════════════════════════════════════


# ── GET /api/sessions ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_sessions(client, db_session, seeded_user):
    """List endpoint returns all sessions for the user, newest first, with jd_count."""
    from app.models import Session as SessionModel, SessionStatus

    s1 = SessionModel(
        user_id=seeded_user.id,
        board="LinkedIn",
        filters="remote",
        search_term="created first",
        status=SessionStatus.active,
    )
    s2 = SessionModel(
        user_id=seeded_user.id,
        board="Indeed",
        filters="hybrid",
        search_term="created second",
        status=SessionStatus.complete,
    )
    db_session.add(s1)
    db_session.add(s2)
    await db_session.commit()
    await db_session.refresh(s1)
    await db_session.refresh(s2)

    # Add 2 JDs to s1, 0 to s2
    for i in range(2):
        jd = JD(
            session_id=s1.id,
            number=i + 1,
            raw_text=f"JD {i}",
            cleaned_text=f"JD {i}",
            company=f"Co {i}",
            role="Eng",
            status=JDStatus.pending,
            status_source=JDStatusSource.ai,
        )
        db_session.add(jd)
    await db_session.commit()

    response = await client.get("/api/sessions")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 2

    # Test ordering logic - Newest first — s2 was created after s1
    assert data[0]["search_term"] == "created second"
    assert data[1]["search_term"] == "created first"
    
    # Test SQLAlchemy select all JDs per session
    assert data[0]["jd_count"] == 0
    assert data[1]["jd_count"] == 2


# ── GET /api/jds/{id}/tailoring ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_tailoring_jobs_for_jd(
    client, db_session, seeded_user, seeded_resume, seeded_session_with_jds,
):
    """Per-JD tailoring history returns all jobs, newest first."""
    _, jd_apply, _ = seeded_session_with_jds

    job1 = TailoringJob(
        jd_id=jd_apply.id,
        resume_id=seeded_resume.id,
        prompt_snapshot="attempt 1",
        status=TailoringStatus.ready,
        model_used="claude-opus-4-6",
    )
    job2 = TailoringJob(
        jd_id=jd_apply.id,
        resume_id=seeded_resume.id,
        prompt_snapshot="attempt 2",
        status=TailoringStatus.queued,
        model_used="claude-opus-4-6",
    )
    db_session.add(job1)
    db_session.add(job2)
    await db_session.commit()

    response = await client.get(f"/api/jds/{jd_apply.id}/tailoring")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 2
    # Both jobs present (order may vary with SQLite, so just check presence)
    statuses = {d["status"] for d in data}
    assert statuses == {"ready", "queued"}


# ── GET /api/sessions/{id}/tailoring-jobs ────────────────────────────────────

@pytest.mark.asyncio
async def test_list_session_tailoring_jobs_dashboard(
    client, db_session, seeded_user, seeded_resume, seeded_session_with_jds,
):
    """Dashboard endpoint returns jobs with JD company/role context."""
    session, jd_apply, _ = seeded_session_with_jds

    job = TailoringJob(
        jd_id=jd_apply.id,
        resume_id=seeded_resume.id,
        prompt_snapshot="dashboard test",
        status=TailoringStatus.processing,
        model_used="claude-opus-4-6",
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    # Did the JOIN work?
    response = await client.get(f"/api/sessions/{session.id}/tailoring-jobs")
    assert response.status_code == 200

    # Do the joined fields show up correctly?
    data = response.json()
    assert len(data) == 1
    assert data[0]["company"] == "Acme Corp"
    assert data[0]["role"] == "Senior Data Engineer"
    assert data[0]["jd_number"] == 1
    assert data[0]["status"] == "processing"


# ── Batch-tailor skip logic ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_batch_tailor_skips_completed_jd(
    client, db_session, seeded_user, seeded_resume, seeded_session_with_jds, seeded_templates,
):
    """JDs with a ready tailoring job are skipped by default."""
    session, jd_apply, _ = seeded_session_with_jds

    # Seed a completed job for jd_apply
    done_job = TailoringJob(
        jd_id=jd_apply.id,
        resume_id=seeded_resume.id,
        prompt_snapshot="already done",
        status=TailoringStatus.ready,
        model_used="claude-opus-4-6",
    )
    db_session.add(done_job)
    await db_session.commit()

    with patch("app.routers.sessions.run_batch_tailor", new_callable=AsyncMock):
        response = await client.post(f"/api/sessions/{session.id}/batch-tailor")

    assert response.status_code == 202

    data = response.json()
    # jd_apply already has a ready job → skipped → 0 new jobs
    assert data["jd_count"] == 0
    assert len(data["jobs"]) == 0


@pytest.mark.asyncio
async def test_batch_tailor_force_retailors_completed_jd(
    client, db_session, seeded_user, seeded_resume, seeded_session_with_jds, seeded_templates,
):
    """force=true creates a new job even when a ready job exists."""
    session, jd_apply, _ = seeded_session_with_jds

    done_job = TailoringJob(
        jd_id=jd_apply.id,
        resume_id=seeded_resume.id,
        prompt_snapshot="already done",
        status=TailoringStatus.ready,
        model_used="claude-opus-4-6",
    )
    db_session.add(done_job)
    await db_session.commit()

    with patch("app.routers.sessions.run_batch_tailor", new_callable=AsyncMock):
        response = await client.post(
            f"/api/sessions/{session.id}/batch-tailor?force=true"
        )

    assert response.status_code == 202

    data = response.json()
    assert data["jd_count"] == 1
    assert len(data["jobs"]) == 1


# ── Pipeline integration test ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_tailoring_pipeline_prompt_to_docx():
    """
    End-to-end tailoring pipeline: prompt assembly → Claude mock → docx_builder → valid docx.

    This is the "silent failures" test from the Sprint 6 spec. It verifies
    that the full chain produces real output — not just that endpoints return
    200 and background tasks get queued.

    Uses StaticPool so all async sessions share the same in-memory database.
    Mocks ClaudeConversation.send() — no real API calls.
    """
    import zipfile
    from io import BytesIO
    from sqlalchemy.pool import StaticPool
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession as SAAsyncSession
    from sqlalchemy.orm import sessionmaker as sa_sessionmaker
    from sqlmodel import SQLModel

    from app.models import (
        User, Resume, Session as SessionModel, SessionStatus,
        JD, JDStatus, JDStatusSource,
        PromptTemplate, PromptPhase,
        TailoringJob, TailoringStatus,
    )
    from app.services.tailoring import run_tailoring_job

    # ── Isolated engine with StaticPool (all connections = same in-memory DB) ──
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    TestSessionLocal = sa_sessionmaker(
        test_engine, class_=SAAsyncSession, expire_on_commit=False
    )

    # ── Seed data ─────────────────────────────────────────────────────────────
    async with TestSessionLocal() as db:
        user = User(auth_token="pipeline-test-token")
        db.add(user)
        await db.commit()
        await db.refresh(user)

        resume = Resume(
            user_id=user.id,
            label="Technical",
            content="Staff engineer with 13+ years building distributed systems at Intel.",
        )
        db.add(resume)
        await db.commit()
        await db.refresh(resume)

        session_model = SessionModel(
            user_id=user.id,
            board="LinkedIn",
            filters="remote",
            search_term="data engineer",
            status=SessionStatus.complete,
        )
        db.add(session_model)
        await db.commit()
        await db.refresh(session_model)

        jd = JD(
            session_id=session_model.id,
            number=1,
            raw_text="We need a senior data engineer with Kafka experience.",
            cleaned_text="We need a senior data engineer with Kafka experience.",
            company="TestCorp",
            role="Senior Data Engineer",
            status=JDStatus.apply,
            status_source=JDStatusSource.ai,
        )
        db.add(jd)
        await db.commit()
        await db.refresh(jd)

        # System-default templates (the minimum: analysis + resume_generation)
        for phase, name, text in [
            (
                PromptPhase.analysis,
                "Analysis",
                "Analyze this JD: {jd_text}\nAgainst these resumes: {resumes}",
            ),
            (
                PromptPhase.resume_generation,
                "Resume Generation",
                "Tailor a resume for {company} — {role}. Compensation: {compensation}",
            ),
        ]:
            t = PromptTemplate(
                user_id=None,
                phase=phase,
                name=name,
                template_text=text,
                version=1,
                is_active=True,
            )
            db.add(t)

        await db.commit()

        # Create the queued job
        job = TailoringJob(
            jd_id=jd.id,
            resume_id=resume.id,
            prompt_snapshot="",  # filled by run_tailoring_job
            status=TailoringStatus.queued,
            model_used="claude-opus-4-6",
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        job_id = job.id

    # ── Mock Claude response (realistic structured JSON) ──────────────────────
    mock_claude_response = json.dumps({
        "analysis": "Strong fit — Kafka experience aligns directly.",
        "strategy": "Emphasize distributed systems and production ownership.",
        "resume": {
            "elements": [
                {"type": "contact_name", "text": "Nicole Rowsey", "font_size": 18},
                {"type": "contact_info", "text": "nicole@example.com | Hillsboro, OR"},
                {"type": "blank_line"},
                {"type": "section_header", "text": "PROFESSIONAL EXPERIENCE"},
                {"type": "job_title", "text": "Staff Data Platform Engineer"},
                {"type": "job_meta", "text": "Intel Corporation | Hillsboro, OR | 2012-2025"},
                {"type": "bullet", "text": "Built Kafka-based reticle inspection automation system processing real-time manufacturing data"},
                {"type": "bullet", "text": "Led 14-engineer cross-functional team delivering distributed data platforms"},
            ]
        }
    })

    mock_send = AsyncMock(return_value=(mock_claude_response, 5000))

    # ── Run the pipeline ──────────────────────────────────────────────────────
    with (
        patch("app.services.tailoring.AsyncSessionLocal", TestSessionLocal),
        patch("app.services.tailoring.ClaudeConversation") as MockConversation,
    ):
        mock_instance = MockConversation.return_value
        mock_instance.send = mock_send
        mock_instance.history = [
            {"role": "user", "content": "assembled prompt"},
            {"role": "assistant", "content": mock_claude_response},
        ]

        await run_tailoring_job(job_id)

    # ── Verify results ────────────────────────────────────────────────────────
    async with TestSessionLocal() as db:
        completed_job = await db.get(TailoringJob, job_id)

        # Status lifecycle: queued → processing → ready
        assert completed_job.status == TailoringStatus.ready
        assert completed_job.completed_at is not None

        # Prompt was assembled and snapshotted (not empty)
        assert len(completed_job.prompt_snapshot) > 0
        assert "Kafka experience" in completed_job.prompt_snapshot  # JD text was substituted

        # Text was extracted from structured elements
        assert completed_job.output_resume is not None
        assert "Nicole Rowsey" in completed_job.output_resume
        assert "Kafka-based" in completed_job.output_resume

        # Docx bytes are a valid zip (docx = zip with XML inside)
        assert completed_job.output_resume_docx is not None
        assert len(completed_job.output_resume_docx) > 0
        buf = BytesIO(completed_job.output_resume_docx)
        assert zipfile.is_zipfile(buf), "output_resume_docx should be a valid zip (docx)"

        # Bonus: python-docx can actually open it (catches corrupted XML)
        from docx import Document
        buf.seek(0)
        doc = Document(buf)
        full_text = "\n".join(p.text for p in doc.paragraphs)
        assert "Nicole Rowsey" in full_text

        # Chat context was persisted for interview prep continuation
        assert completed_job.chat_context is not None
        assert len(completed_job.chat_context) == 2  # user + assistant

    # ── Cleanup ───────────────────────────────────────────────────────────────
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await test_engine.dispose()
