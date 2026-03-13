# Completed Sprints — Phase 0

> Execution order: bottom-up (first sprint is at the bottom)

---

## Sprint 10 — Frontend: SSE + Cards 3/13/2026
`application-pipeline-20260313-1544`

The first sprint where the app *does the thing* in the browser. Three pieces shipped: the analyze trigger, the SSE consumer, and the card animations.

**Analyze button on Tab 1.** SessionDetailPage gained an "Analyze" button that calls `analyzeSession()` and disables during analysis. Error handling: 422 "no resumes" shows an amber banner with a link to /resumes; API/SSE failures show a red banner with a retry button.

**SSE consumer hook** (`useSSE.js`). Reads the `text/event-stream` response from `analyzeSession()`. Dispatches `batch_start`, `jd_result`, `batch_complete`, and `analysis_complete` events to update JD state and meta-analysis in real time. Stateless — owns zero `useState`, all mutation lives in the caller's callbacks. Buffer-splits on `\n\n` with the classic split/pop pattern for chunked network reads.

**Card animations.** Cards start gray (pending), animate to green/yellow/red as `jd_result` events arrive via CSS `transition-all duration-500`. Status-dependent glow on Apply and Maybe cards; No cards recede. Meta-analysis panel (`MetaAnalysis.jsx`) updates live after each `batch_complete` — collapsible, whitespace-pre-wrap. Summary chips (N apply · N maybe · N no) appear after `analysis_complete`. The "show a non-engineer" moment.

**State layering.** During streaming, `jdOverrides` holds partial updates from `jd_result` events, merged on top of context jds for rendering. After `analysis_complete`, `refreshSession()` pulls canonical state from the backend and the overrides become redundant (harmless — same data).

**Tests**: SessionDetailPage.test.jsx expanded — integration tests covering session fetch, JD paste flow, card grid, analyze button states, error/warning banners. useSSE.test.js — parseSSEMessage unit tests + consume integration test against a fake readable stream.

Housekeeping shipped:
- [x] `analyzeSession()` in client.js had a phantom `resume_id` body param the backend ignores. Fixed: `analyzeSession(sessionId)` with no body, raw `fetch()` returning the Response for SSE consumption. (First sprint where this function is called from UI — natural place to catch it.)


## Sprint 9 — Frontend: Resume Management + Nullable resume_id Fix 3/12/2026
`application-pipeline-20260312-2108`

Two things shipped together: the Resumes page UI and a backend schema fix for resume deletion safety.

**Frontend — ResumesPage.jsx** (no longer a stub): list of resume cards with create/edit/delete. ResumeForm.jsx (text area + label, handles both create and edit modes). ResumeCard.jsx (label, preview, edit/delete buttons with confirmation). 3-resume cap enforced visually (disabled button, "3/3" counter). All state lives in ResumesPage; child components call back up via props.

**Backend — nullable resume_id on TailoringJob**: `resume_id` changed from `UUID` (required) to `UUID | None` with `ondelete=SET NULL`. Migration `b30f639f830c`. Deleting a resume no longer breaks tailoring job FK constraints — the FK goes null but `prompt_snapshot`, `output_resume`, and `output_resume_docx` remain intact. Response models in jds.py and sessions.py updated to `UUID | None`. See ADR-017 for the full snapshot architecture this feeds into (Phase 1+).

**Tests**: ResumesPage.test.jsx — 8 tests covering load/display, create flow, edit flow, delete with confirmation, 3-resume cap UI, error states.

Done when: you can manage resumes entirely through the UI, and deleting a resume doesn't cascade-break existing tailoring jobs.


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


## Sprint 7 — Frontend Shell 3/9/2026 4:00p
`application-pipeline-20260309`

Stood up the React app for real. All scaffolding, no features — working app shell with routing, an API client, and Tailwind v4 for styling.

- CSS framework decision: **Tailwind v4** (CSS-first config via `@theme` in index.css, `@tailwindcss/vite` plugin — no tailwind.config.js)
- App layout: top nav with tab links, routed page stubs (Sessions, Calibrate, Review, Tailoring, Resumes)
- `api/client.js`: fetch wrappers for all existing backend routes (sessions, JDs, resumes, tailoring)
- Dev proxy: Vite → FastAPI (`/api/*` and `/health` proxied, no CORS in dev)
- Vitest + Testing Library + jsdom: 3 shell/routing tests in `App.test.jsx`
- react-router-dom v7, React 19


# Sprint 6 — Backend Catchup 3/6/2026 11:08a
`application-pipeline-20260306-1110`
- `GET /api/sessions` — list all sessions for current user (session picker prerequisite)
- `GET /api/sessions/{id}/tailoring-jobs` — batch status dashboard (Tab 4 prerequisite)
- `GET /api/jds/{id}/tailoring` — per-JD tailoring history (Tab 4 prerequisite)
- Batch-tailor: skip JDs that already have a completed tailoring job unless `force=true`
- One targeted integration test for the tailoring pipeline (prompt assembly → Claude mock → docx_builder → valid docx bytes). Silent failures here are harder to catch by eye than a bad SSE stream.


# Sprint 5 - Plumbing 3/4/2026 7:32p - 9:19p
Resume CRUD (POST, GET, PATCH, DELETE /api/resumes). PATCH /jds/{id} and GET /jds/{id}. Wire routers in main.py. Goal: no more manual psql seeding.


# Sprint 4 - Claude batch analysis service + SSE (~4–5 hours) 3/4/3026 3:05p-5:03p
`application-pipeline-20260304-1703`
services/claude.py, services/analysis.py, POST /sessions/{id}/analyze.
This is the first "it actually does the thing" moment — JDs go in, analysis comes back. The SSE plumbing is the trickiest part (event streaming + batching logic).
This is going to require more time that the previous sprints. This is also where the core value proposition becomes testable for real.


# Sprint 3 - Tests? PyTest? Now? Yes 3/4/2026 2:51p-3:04p 
`application-pipeline-20260304-1504`
-backend/tests/
	- test_sessions.py
	- test_text_cleaning.py


# Sprint 2 - Text cleaning + Session/JD routes (~2–3 hours) 3/4/2026 12:51p,lunch,2:50p!(and test above)
`application-pipeline-20260304-1504`
text_cleaning.py + POST /sessions, POST /sessions/{id}/jds, GET /sessions/{id}. This is the data entry path — the moment you can actually paste a JD and get it back out. Also the first real test of your models against Postgres. Worth doing before Claude integration so you're not debugging the ORM and the API client at the same time.


# Sprint 1 - build models 2/28/2026
`application-pipeline-20260228`
I'm building ApplicationPipeline. The docs describe the full design. I want to start Phase 0: FastAPI backend with SQLModel entities, Alembic migrations, text cleaning utility, and Claude API integration for batch analysis. My repo is scaffolded with backend/ and frontend/ directories. Let's start with the SQLModel models in backend/app/models.py.