"""
tests/test_sessions.py

Integration tests for the data entry path.
These need a test DB and async test client — skipped until the schema is stable
and you're ready to wire up pytest-asyncio + httpx.

Setup you'll need when you uncomment:
    pip install pytest-asyncio httpx

    conftest.py (create this in tests/):
        import pytest
        from httpx import AsyncClient, ASGITransport
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker
        from sqlmodel import SQLModel

        from app.main import app
        from app.database import get_session
        from app.models import User

        TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

        @pytest.fixture
        async def db_session():
            engine = create_async_engine(TEST_DATABASE_URL)
            async with engine.begin() as conn:
                await conn.run_sync(SQLModel.metadata.create_all)
            AsyncTestSession = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            async with AsyncTestSession() as session:
                yield session
            async with engine.begin() as conn:
                await conn.run_sync(SQLModel.metadata.drop_all)

        @pytest.fixture
        async def seeded_user(db_session):
            user = User(auth_token="test-token")
            db_session.add(user)
            await db_session.commit()
            await db_session.refresh(user)
            return user

        @pytest.fixture
        async def client(db_session):
            async def override_get_session():
                yield db_session
            app.dependency_overrides[get_session] = override_get_session
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
                yield c
            app.dependency_overrides.clear()

Run with: pytest tests/test_sessions.py -v
"""

import pytest


# ── POST /api/sessions ────────────────────────────────────────────────────────

@pytest.mark.skip(reason="wire up conftest.py first")
@pytest.mark.asyncio
async def test_create_session_returns_201(client, seeded_user):
    response = await client.post("/api/sessions", json={
        "board": "LinkedIn",
        "filters": "remote, last 24 hours",
        "search_term": "data engineer",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["board"] == "LinkedIn"
    assert data["jd_count"] == 0
    assert data["status"] == "active"


@pytest.mark.skip(reason="wire up conftest.py first")
@pytest.mark.asyncio
async def test_create_session_strips_whitespace(client, seeded_user):
    response = await client.post("/api/sessions", json={
        "board": "  LinkedIn  ",
        "filters": "remote",
        "search_term": "  data engineer  ",
    })
    data = response.json()
    assert data["board"] == "LinkedIn"
    assert data["search_term"] == "data engineer"


# ── POST /api/sessions/{id}/jds ───────────────────────────────────────────────

@pytest.mark.skip(reason="wire up conftest.py first")
@pytest.mark.asyncio
async def test_add_jd_returns_201_with_cleaned_text(client, seeded_user):
    session = (await client.post("/api/sessions", json={
        "board": "LinkedIn", "filters": "remote", "search_term": "data engineer"
    })).json()

    response = await client.post(f"/api/sessions/{session['id']}/jds", json={
        "raw_text": "Senior\xa0Data\xa0Engineer\r\n\r\n\r\nWe are hiring.",
        "company": "Acme",
        "role": "Senior Data Engineer",
    })
    assert response.status_code == 201
    data = response.json()
    assert "\xa0" not in data["cleaned_text"]
    assert "\r" not in data["cleaned_text"]
    assert data["number"] == 1
    assert data["status"] == "pending"
    assert data["status_source"] == "ai"


@pytest.mark.skip(reason="wire up conftest.py first")
@pytest.mark.asyncio
async def test_add_jd_numbers_sequentially(client, seeded_user):
    session = (await client.post("/api/sessions", json={
        "board": "LinkedIn", "filters": "remote", "search_term": "data engineer"
    })).json()

    for i in range(1, 4):
        r = await client.post(f"/api/sessions/{session['id']}/jds", json={
            "raw_text": f"JD number {i} with enough text to survive cleaning."
        })
        assert r.json()["number"] == i


@pytest.mark.skip(reason="wire up conftest.py first")
@pytest.mark.asyncio
async def test_add_jd_empty_after_cleaning_returns_422(client, seeded_user):
    session = (await client.post("/api/sessions", json={
        "board": "LinkedIn", "filters": "remote", "search_term": "data engineer"
    })).json()

    response = await client.post(f"/api/sessions/{session['id']}/jds", json={
        "raw_text": "\xa0\u200b\u200c",   # nothing left after cleaning
    })
    assert response.status_code == 422


@pytest.mark.skip(reason="wire up conftest.py first")
@pytest.mark.asyncio
async def test_25_jd_cap_returns_409(client, seeded_user):
    session = (await client.post("/api/sessions", json={
        "board": "LinkedIn", "filters": "remote", "search_term": "data engineer"
    })).json()

    for _ in range(25):
        await client.post(f"/api/sessions/{session['id']}/jds", json={
            "raw_text": "Filler JD text that is long enough to survive cleaning."
        })

    response = await client.post(f"/api/sessions/{session['id']}/jds", json={
        "raw_text": "One too many."
    })
    assert response.status_code == 409


# ── Ownership / auth ──────────────────────────────────────────────────────────

@pytest.mark.skip(reason="wire up conftest.py first")
@pytest.mark.asyncio
async def test_get_session_wrong_id_returns_404(client, seeded_user):
    response = await client.get("/api/sessions/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.skip(reason="wire up conftest.py first")
@pytest.mark.asyncio
async def test_add_jd_to_wrong_session_returns_404(client, seeded_user):
    response = await client.post(
        "/api/sessions/00000000-0000-0000-0000-000000000000/jds",
        json={"raw_text": "Some job description text."}
    )
    assert response.status_code == 404


# ── GET /api/sessions/{id} ────────────────────────────────────────────────────

@pytest.mark.skip(reason="wire up conftest.py first")
@pytest.mark.asyncio
async def test_get_session_returns_jds_in_order(client, seeded_user):
    session = (await client.post("/api/sessions", json={
        "board": "LinkedIn", "filters": "remote", "search_term": "data engineer"
    })).json()

    for text in ["First JD text here.", "Second JD text here.", "Third JD text here."]:
        await client.post(f"/api/sessions/{session['id']}/jds", json={"raw_text": text})

    response = await client.get(f"/api/sessions/{session['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["jd_count"] == 3
    numbers = [jd["number"] for jd in data["jds"]]
    assert numbers == [1, 2, 3]
