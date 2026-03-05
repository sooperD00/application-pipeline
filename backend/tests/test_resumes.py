"""
tests/test_resumes.py

Integration tests for Resume CRUD.
Depends on conftest.py for db_session, seeded_user, and client fixtures.

Run with: pytest tests/test_resumes.py -v
"""

import pytest


# ── POST /api/resumes ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_resume_returns_201(client, seeded_user):
    response = await client.post("/api/resumes", json={
        "label": "Technical",
        "content": "Nicole Doe\n10+ years distributed systems...",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["label"] == "Technical"
    assert "10+ years" in data["content"]
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_resume_strips_whitespace_on_label(client, seeded_user):
    response = await client.post("/api/resumes", json={
        "label": "  Leadership  ",
        "content": "Some leadership experience here.",
    })
    assert response.status_code == 201
    assert response.json()["label"] == "Leadership"


@pytest.mark.asyncio
async def test_create_resume_empty_label_returns_422(client, seeded_user):
    response = await client.post("/api/resumes", json={
        "label": "   ",
        "content": "Some content.",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_resume_empty_content_returns_422(client, seeded_user):
    response = await client.post("/api/resumes", json={
        "label": "Technical",
        "content": "   ",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_resume_enforces_3_cap(client, seeded_user):
    for i in range(3):
        r = await client.post("/api/resumes", json={
            "label": f"Version {i + 1}",
            "content": f"Resume content for version {i + 1}.",
        })
        assert r.status_code == 201

    # Fourth should be rejected
    response = await client.post("/api/resumes", json={
        "label": "Too Many",
        "content": "This one should be rejected.",
    })
    assert response.status_code == 409


# ── GET /api/resumes ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_resumes_empty(client, seeded_user):
    response = await client.get("/api/resumes")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_resumes_returns_all_in_order(client, seeded_user):
    labels = ["Technical", "Leadership", "Concise"]
    for label in labels:
        await client.post("/api/resumes", json={
            "label": label,
            "content": f"{label} resume content.",
        })

    response = await client.get("/api/resumes")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert [r["label"] for r in data] == labels


# ── PATCH /api/resumes/{id} ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_patch_label(client, seeded_user):
    created = (await client.post("/api/resumes", json={
        "label": "Old Label",
        "content": "Some resume content.",
    })).json()

    response = await client.patch(f"/api/resumes/{created['id']}", json={
        "label": "New Label",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["label"] == "New Label"
    assert data["content"] == "Some resume content."  # unchanged


@pytest.mark.asyncio
async def test_patch_content(client, seeded_user):
    created = (await client.post("/api/resumes", json={
        "label": "Technical",
        "content": "Original content.",
    })).json()

    response = await client.patch(f"/api/resumes/{created['id']}", json={
        "content": "Updated resume with new bullets.",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Updated resume with new bullets."
    assert data["label"] == "Technical"  # unchanged


@pytest.mark.asyncio
async def test_patch_wrong_id_returns_404(client, seeded_user):
    response = await client.patch(
        "/api/resumes/00000000-0000-0000-0000-000000000000",
        json={"label": "Ghost"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_patch_empty_label_returns_422(client, seeded_user):
    created = (await client.post("/api/resumes", json={
        "label": "Technical",
        "content": "Content here.",
    })).json()

    response = await client.patch(f"/api/resumes/{created['id']}", json={
        "label": "   ",
    })
    assert response.status_code == 422


# ── DELETE /api/resumes/{id} ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_resume_returns_204(client, seeded_user):
    created = (await client.post("/api/resumes", json={
        "label": "Technical",
        "content": "Some resume content.",
    })).json()

    response = await client.delete(f"/api/resumes/{created['id']}")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_frees_cap_slot(client, seeded_user):
    ids = []
    for i in range(3):
        r = await client.post("/api/resumes", json={
            "label": f"Version {i + 1}",
            "content": f"Content for version {i + 1}.",
        })
        ids.append(r.json()["id"])

    # At cap — delete one
    await client.delete(f"/api/resumes/{ids[0]}")

    # Should now be able to add again
    response = await client.post("/api/resumes", json={
        "label": "Replacement",
        "content": "Freed up a slot.",
    })
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_delete_wrong_id_returns_404(client, seeded_user):
    response = await client.delete("/api/resumes/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_removes_from_list(client, seeded_user):
    created = (await client.post("/api/resumes", json={
        "label": "Technical",
        "content": "Some resume content.",
    })).json()

    await client.delete(f"/api/resumes/{created['id']}")

    response = await client.get("/api/resumes")
    assert response.json() == []
