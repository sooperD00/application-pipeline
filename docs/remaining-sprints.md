# Remaining Sprints — Phase 0

> Execution order: top-down. Next sprint is at the top.

---


## Sprint 8 — Frontend: Session + JD Flow

Session creation form (board, filters, search_term). JD paste flow: text area, submit, card appears. Card display: number, company, role, gray (pending). Session picker using `GET /api/sessions`.

Done when: you can create a session and paste JDs through the UI, and see them as cards.


## Sprint 9 — Frontend: SSE + Cards

SSE consumer hook (`useSSE.js`). Cards animate green/yellow/red as analysis returns. Meta-analysis panel updates after each batch. The "show a non-engineer" moment.


## Sprint 10 — Frontend: Resume Management

Resume paste, edit, label, delete. The `GET/POST/PATCH/DELETE /api/resumes` backend is done (Sprint 5) — this is just the UI. Prerequisite for Tab 4: tailoring needs at least one resume to exist, and right now the only way to create one is Swagger or the seed script.

Simple page: list of resume cards, "Add Resume" button → text area + label field, inline edit, delete with confirmation. Enforce the 3-resume cap visually (disable the button, show "3/3").


## Sprint 11 — Frontend: Tab 4 (Tailoring)

Tailoring kickoff UI per JD. Status polling (queued → processing → ready) using `GET /sessions/{id}/tailoring-jobs`. Output view: resume text, cover letter, app answers. Download button for docx.

- Zip download: `GET /api/jds/{id}/tailoring/{job_id}/package` — bundles resume.docx + jd.txt + cover_letter.txt + app_questions.txt + analysis.txt + notes.txt into one zip (ADR-014). ~40 lines in jds.py, no new deps. Add `downloadTailoringPackage` to api/client.js.

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
- [ ] Nav doesn't show session-scoped tabs (1-4) vs global tabs (Resumes) differently — Sprint 8 will restructure when session context exists
- [ ] No 404 catch-all route — add in Sprint 8 when there's a real page to show
- [ ] api/client.js has no retry logic or token refresh — Phase 1 (auth)
- [ ] Tailwind @theme uses Inter/JetBrains Mono but doesn't load them from Google Fonts — add <link> to index.html when you care about typography (Sprint 8+, or never if system fonts are fine)