"""
tests/test_analysis.py

stream_analysis marks a session `analyzing` before its first Claude call. These tests pin what
happens when a run stops early, which is what a browser leaving the page does: Starlette either
closes the generator at its next yield, or cancels it mid-await through an anyio task group.
Either way the session has to come back `active`. Otherwise the Analyze button stays disabled
and the endpoint answers 409 for good.

Claude is mocked; nothing here calls the API. [s-2716d1-a] adds the happy-path batching, event
order and retry tests to this file.

Run:
    pytest tests/test_analysis.py -v
"""

import json

import anyio
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.models import JD, Resume, Session as SessionModel, SessionStatus, User
from app.services import analysis
from app.services.claude import ClaudeConversation


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
async def factory(tmp_path, monkeypatch):
    """One file-backed SQLite DB for both the request's session and the cleanup's.

    The cleanup opens its own session from analysis.AsyncSessionLocal, so it has to reach the
    same database the test wrote to. An in-memory DB is private to its engine, so a file it is.
    """
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'analysis.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    make = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    monkeypatch.setattr(analysis, "AsyncSessionLocal", make, raising=False)
    yield make
    await engine.dispose()


@pytest.fixture
async def ready_session(factory):
    """A user with one resume and an `active` session holding one JD."""
    async with factory() as db:
        user = User(auth_token="test-token")
        db.add(user)
        await db.commit()
        await db.refresh(user)

        db.add(Resume(user_id=user.id, label="Technical", content="resume text"))
        session = SessionModel(
            user_id=user.id, board="LinkedIn", filters="remote", search_term="backend",
            status=SessionStatus.active,
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

        db.add(JD(session_id=session.id, number=1, raw_text="jd", cleaned_text="jd", company="Co"))
        await db.commit()
        return session.id, user


async def _status(factory, session_id) -> SessionStatus:
    async with factory() as db:
        return (await db.get(SessionModel, session_id)).status


def _claude_that_never_answers(monkeypatch) -> anyio.Event:
    """Replace send() with a call that hangs. The returned event is set once it's waiting."""
    waiting = anyio.Event()

    async def send(self, message):
        waiting.set()
        await anyio.sleep_forever()

    monkeypatch.setattr(ClaudeConversation, "send", send)
    return waiting


# ── Interrupted runs ─────────────────────────────────────────────────────────


async def test_closing_the_stream_mid_run_leaves_session_active(factory, ready_session, monkeypatch):
    """The browser leaves between events, so Starlette closes the generator at a yield."""
    _claude_that_never_answers(monkeypatch)
    session_id, user = ready_session

    async with factory() as db:
        stream = analysis.stream_analysis(session_id, db, user)
        assert (await stream.__anext__()).startswith("event: batch_start")
        assert await _status(factory, session_id) == SessionStatus.analyzing
        await stream.aclose()

    assert await _status(factory, session_id) == SessionStatus.active


async def test_cancelling_during_the_claude_call_leaves_session_active(factory, ready_session, monkeypatch):
    """The browser leaves mid-call, so Starlette cancels the stream's task group.

    anyio re-cancels every await inside a cancelled scope. An unshielded reset in the cleanup
    never finishes, and this test stays red until the reset is shielded.
    """
    waiting = _claude_that_never_answers(monkeypatch)
    session_id, user = ready_session

    async with factory() as db:
        async def consume():
            async for _ in analysis.stream_analysis(session_id, db, user):
                pass

        async with anyio.create_task_group() as tg:
            tg.start_soon(consume)
            await waiting.wait()
            tg.cancel_scope.cancel()

    assert await _status(factory, session_id) == SessionStatus.active


# ── A run that finishes ──────────────────────────────────────────────────────


async def test_a_finished_run_stays_complete(factory, ready_session, monkeypatch):
    """The cleanup only touches a session still at `analyzing`, so it can't undo a finished run."""
    async def send(self, message):
        reply = {
            "results": [{"jd_number": 1, "status": "apply", "analysis": "fit", "requirements_met": []}],
            "meta_analysis": "summary",
        }
        return json.dumps(reply), 10

    monkeypatch.setattr(ClaudeConversation, "send", send)
    session_id, user = ready_session

    async with factory() as db:
        events = [event async for event in analysis.stream_analysis(session_id, db, user)]

    assert events[-1].startswith("event: analysis_complete")
    assert await _status(factory, session_id) == SessionStatus.complete
