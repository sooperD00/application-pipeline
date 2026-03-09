# Remaining Sprints — Phase 0

> Execution order: top-down. Next sprint is at the top.

---


## Sprint 8 — Frontend: Session + JD Flow

Session context lives in the URL (`/sessions/:id`); tabs 1–4 become nested routes under `:id`, Resumes stays global at `/resumes`.

Route structure:

```
/sessions                     ← picker/list (global)
/sessions/:id                 ← session detail/dashboard (Tab 1)
/sessions/:id/calibrate       ← Tab 2
/sessions/:id/review          ← Tab 3
/sessions/:id/tailor          ← Tab 4
/resumes                      ← stays global, no session prefix
```

Why URL params over a context provider: (1) state survives refresh, bookmarks, and Cmd+click to new tab — table stakes for a daily-use productivity tool; (2) react-router-dom v7 nested routes are purpose-built for this, so session-scoped components just call `useParams()` with no prop drilling or null-context guards; (3) every downstream sprint that adds a session-scoped feature just reads `useParams().sessionId` instead of handling the "no session selected" edge case in component code. The session picker dropdown can still live in the nav — it just navigates to `/sessions/:id/...` on select instead of setting state.

Deliverables: session creation form (board, filters, search_term). JD paste flow: text area, submit, card appears. Card display: number, company, role, gray (pending). Session picker using `GET /api/sessions`. Restructure App.jsx routing from flat routes to nested layout. 404 catch-all route.

Done when: you can create a session, paste JDs through the UI, see them as cards, and refresh the page without losing your place.


## Sprint 9 — Frontend: Resume Management

Resume paste, edit, label, delete. The `GET/POST/PATCH/DELETE /api/resumes` backend is done (Sprint 5) — this is just the UI. Prerequisite for Tab 4: tailoring needs at least one resume to exist, and right now the only way to create one is Swagger or the seed script.

Simple page: list of resume cards, "Add Resume" button → text area + label field, inline edit, delete with confirmation. Enforce the 3-resume cap visually (disable the button, show "3/3").

(Moved ahead of SSE sprint so the full paste-JDs → pick-resume → analyze flow is testable end-to-end the moment SSE lands.)


## Sprint 10 — Frontend: SSE + Cards

SSE consumer hook (`useSSE.js`). Cards animate green/yellow/red as analysis returns. Meta-analysis panel updates after each batch. The "show a non-engineer" moment.


## Sprint 11 — Frontend: Tab 4 (Tailoring)

Tailoring kickoff UI per JD. Status polling (queued → processing → ready) using `GET /sessions/{id}/tailoring-jobs`. Output view: resume text, cover letter, app answers. Download button for docx.

- Zip download: `GET /api/jds/{id}/tailoring/{job_id}/package` — bundles resume.docx + jd.txt + cover_letter.txt + app_questions.txt + analysis.txt + notes.txt into one zip (ADR-014). ~40 lines in jds.py, no new deps. Add `downloadTailoringPackage` to api/client.js.

Context load for this sprint: `jds.py` (389 lines), `tailoring.py` (362 lines), `client.js` (209 lines), plus the new TailoringPage — ~1000 lines of backend reference alongside new frontend work. Fits one context window but it's the heaviest sprint in the plan.

Housekeeping that fits naturally here:
- [ ] batch-tailor skip logic doesn't account for processing/queued jobs (could create duplicates if you double-click "Apply All" fast) — real concern now that there's a UI button


## Sprint 12 — Deploy to Railway

Environment variables, Alembic migration on prod DB, CORS for prod domain. Half-session if nothing is on fire.

Critical: **run the seed script** (or equivalent migration) on first deploy. `run_tailoring_job` checks for the `resume_generation` PromptTemplate and silently bails if it's missing (line 291 of tailoring.py). A fresh DB with just `alembic upgrade head` gives you empty template tables and tailoring that does nothing. Either:
- Add seed data to an Alembic data migration, or
- Document `python -m scripts.seed` as a required post-deploy step


## Sprint 13 — Tests

Audit test coverage, fill gaps. Priority: `test_analysis.py` (batching logic, error/retry with mocked Claude client), then anything needed for multi-user safety in Phase 1.

---

## Deferred from Phase 0

**Activities** (`routers/activities.py`, `services/activities.py`): The data model is in place (Activity table, ActivityType enum, cascade templates designed in service-layer-notes.md), but no router, service, or frontend exists. The README tree and architecture.md list these as Phase 0 scope, but they aren't needed for the core flow (paste → analyze → tailor → download). Deferring to Phase 1 when the Full Tracker makes them visible and useful.

**Prompts directory** (`backend/app/prompts/`): Placeholder for extracting system prompts from hardcoded strings in `services/analysis.py` and `services/tailoring.py` to files. See ADR-013 — this is about IP protection before the repo gets public attention, not about functionality. Deferred past MVP.

---

## Housekeeping (any sprint)

- [ ] `datetime.utcnow()` deprecation warnings — switch to `datetime.now(datetime.UTC)` across models.py and tailoring.py
- [ ] `HTTP_422_UNPROCESSABLE_ENTITY` deprecation — FastAPI renamed to `HTTP_422_UNPROCESSABLE_CONTENT`
- [ ] Timestamps showing 1 day ahead in Oregon (UTC storage, no timezone conversion). Not important for MVP (Nicole is only user), but will confuse anyone else.
- [ ] assets/react.svg and public/vite.svg still in tree — harmless, clean up whenever
- [ ] api/client.js has no retry logic or token refresh — Phase 1 (auth)
- [ ] Tailwind @theme uses Inter/JetBrains Mono but doesn't load them from Google Fonts — add <link> to index.html when you care about typography (Sprint 8+, or never if system fonts are fine)