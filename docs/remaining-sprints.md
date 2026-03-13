# Remaining Sprints — Phase 0

> Execution order: top-down. Next sprint is at the top.

---


## Sprint 11 — Frontend: Tab 4 (Tailoring)

Tailoring kickoff UI per JD. Status polling (queued → processing → ready) using `GET /sessions/{id}/tailoring-jobs`. Output view: resume text, cover letter, app answers. Download button for docx.

- Zip download: `GET /api/jds/{id}/tailoring/{job_id}/package` — bundles resume.docx + jd.txt + cover_letter.txt + app_questions.txt + analysis.txt + notes.txt into one zip (ADR-014). ~40 lines in jds.py, no new deps. Add `downloadTailoringPackage` to api/client.js.

Context load for this sprint: `jds.py` (389 lines), `tailoring.py` (362 lines), `sessions.py` (538 lines — dashboard endpoint, batch-tailor phantom fix, stale Sprint 9 comment), `models.py` (291 lines — `failed` enum addition), `client.js` (~210 lines), plus the new TailoringPage — ~1,800 lines of existing reference alongside new frontend work. Fits one Opus 4.6 context window but it's the heaviest sprint in the plan.

Housekeeping that fits naturally here:
- [ ] batch-tailor skip logic doesn't account for processing/queued jobs (could create duplicates if you double-click "Apply All" fast) — real concern now that there's a UI button
- [ ] `batchTailor()` in client.js sends a phantom `resume_id` body param, same issue `analyzeSession()` had (fixed in Sprint 10). The backend's `batch_tailor_session` takes no body model — it fetches all user resumes internally and picks `resumes[0].id` for the FK. Fix: drop the body, simplify to `batchTailor(sessionId, { force })`.
- [ ] `createTailoringJob()` in client.js sends `{ resume_id }` but the backend endpoint (jds.py line 259) takes no body — same phantom pattern. First sprint where single-JD tailoring is called from UI. Fix: `createTailoringJob(jdId)` with no body.
- [ ] `sessions.py` line 376 and `jds.py` line 222 both say "Tab 4 prerequisite (Sprint 9)" — should be Sprint 11 after the reshuffle. Fix while you're already in those files.
- [ ] `resume_id` on tailoring jobs can now be null (Sprint 9 — source resume deleted after tailoring ran). `TailoringJobRead` and `TailoringJobDashboardRead` both expose `UUID | None`. TailoringPage needs to handle this gracefully — show "Source resume deleted" or omit the label. One-liner but easy to miss if it's not in the spec.
- [ ] **Add `failed` to `TailoringStatus` enum.** Currently only `queued`, `processing`, `ready`, `reviewed` — no failure state. If the Claude API errors out or the `resume_generation` PromptTemplate is missing, `run_tailoring_job` silently returns and the job sits at `queued` forever. With a polling UI, "perpetually queued" is indistinguishable from "dead." Fix: add `failed` value (one-line Alembic migration), set it in the error paths in tailoring.py, show it in the TailoringPage UI. This is the sprint where the stuck-job UX becomes visible, so this is where it belongs.


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

**Resume selection for tailoring.** Phase 0 sends all of the user's resumes (up to 3) to Claude for every analysis and tailoring call. Claude sees all versions and decides what to emphasize, blend, or draw from based on the JD — this is the intended default behavior and should remain the default in all phases. Claude is better and faster at picking the right resume emphasis for a given role than a human skimming three documents, and blending across versions is something a human can't do at all.

Phase 1+ adds an optional override: per-JD resume picker in the Tab 4 kickoff modal where the user can select a single resume or a subset instead of sending all three. Backend changes: add an optional `resume_ids` body param to the analyze and batch-tailor endpoints, filter the resume query when present, fall back to "all resumes" when absent. Frontend: resume chip selector in the tailoring kickoff UI, default state = "All (Claude picks)". The `resume_id` FK on TailoringJob already exists for tracking which resume was primary — Phase 1 makes it meaningful by letting the user constrain the input set.

(Note: `analyzeSession()`, `batchTailor()`, and `createTailoringJob()` in client.js were scaffolded with a `resume_id` parameter anticipating this feature. The backend endpoints never accepted it — they fetch all resumes internally. The phantom params are cleaned up in Sprint 10 (`analyzeSession`) and Sprint 11 (`batchTailor`, `createTailoringJob`) respectively. When resume selection is implemented, the parameter comes back with real plumbing behind it.)

**Resume snapshot architechture** see ADR-017
session_resume_snapshots table, session locking, clone session. Phase 1+.
ADR, a new table, migrations, service changes, and frontend work - a full context window (large sprint).

---

## Housekeeping (any sprint)

- [ ] `datetime.utcnow()` deprecation warnings — switch to `datetime.now(datetime.UTC)` across models.py and tailoring.py
- [ ] `HTTP_422_UNPROCESSABLE_ENTITY` deprecation — FastAPI renamed to `HTTP_422_UNPROCESSABLE_CONTENT`
- [ ] Timestamps showing 1 day ahead in Oregon (UTC storage, no timezone conversion). Not important for MVP (Nicole is only user), but will confuse anyone else.
- [ ] assets/react.svg and public/vite.svg still in tree — harmless, clean up whenever
- [ ] api/client.js has no retry logic or token refresh — Phase 1 (auth)
- [ ] Tailwind @theme uses Inter/JetBrains Mono but doesn't load them from Google Fonts — add <link> to index.html when you care about typography (or never if system fonts are fine)
- [ ] add press enter to submit form on SessionsPage.jsx (a simple wrap that Claude can do)
- [ ] ability to Edit/Delete JD cards in sessions/:id (use same implementation as for edit/delete resume cards)
- [ ] Card grid sort: after analysis starts, sort by [status_priority, number] instead of just number. Apply cards float to top after each batch_complete, giving the user real-time feedback on which JDs survived. Toggle: sort by number when status=active (paste order matters during data entry), sort by status when analyzing/complete. Small change in SessionDetailPage's mergedJds sort comparator.
- [ ] make the JD cards have an aspect ratio like an actual playing card (right now it's longer horizontally); then, make them in a ribbon spread instead of currently they don't overalp at all. Use ~generous and equal spacing at first (before analysis) so user can see beginning of title/subtitle. But then after analysis, make the "Apply" cards trickled to the left not overlapping, then ribbon spread the "maybe" results in the middle with medium overlap, and ribon spred the "no" results with very tight spacing / high overlap on the right.
- [ ] analyzeSession() currently has no AbortController integration — if the user navigates away mid-stream, useSSE.abort() cancels the reader but doesn't abort the fetch itself. The backend stream_analysis generator will continue running until it finishes or the connection drops. Harmless for single-user MVP (the results still write to DB correctly), but wasteful. Add AbortController to the fetch call in Sprint 11 (already in client.js) or Phase 1.
- [ ] MetaAnalysis text is rendered as whitespace-pre-wrap plain text. If Claude's meta_analysis includes markdown formatting (bold, lists), it won't render. Could add a lightweight markdown renderer later, but plain text is fine for MVP — the analysis prompt doesn't ask for markdown.
- [ ] The Analyze button always says "Analyze" even for re-analysis. Could say "Re-analyze" when session.status === 'complete'. Polish, not function.


## Tech Debt
- [ ] Phase 1+: extract repeated Tailwind class strings into shared component styles.
- [ ] Phase 1+: extract shared test factories and mocks once data models stabilize, espcially if same factory/mock appears in 3+ test files and the shape is identical. `__tests__/factories.js` and `__tests__/mocks.js`
- [ ] tooltip "Select or create a session to unlock this step" appears after 1s delay = browser-native `title` attribute behavior (delay hardcoded in the browser, not my app). Add a custom tooltip component to make it ~instant (polish)
- [ ] Phase 1: SessionLayout fetch has no retry/error-retry UX — user must manually navigate away and back on transient errors. Fine for single-user MVP; Phase 1 adds retry button.
- [ ] Phase 1: The session picker is the /sessions list page (click a row to enter). A nav dropdown picker was mentioned in sprint spec — deferred; the list page approach is simpler and sufficient. If dropdown is wanted later, it reads from the same listSessions() endpoint.
- [ ] Phase 1: No loading skeleton / optimistic UI on addJD — the card grid waits for refreshSession() to resolve. Acceptable latency for local dev; may want optimistic insert for prod. Phase 1.
- [ ] Phase 1: No "unsaved changes" guard on the form — if you click Edit while mid-create, the form overwrites silently. Acceptable for single-user MVP; revisit in Phase 1 multi-user.
- [ ] Phase N. line-clamp-3 depends on -webkit-line-clamp which is non-standard but supported in all modern browsers. If it ever breaks, fall back to a JS truncation.
- [ ] Phase N: observe behavior post-launch. The Analyze button re-enables immediately on error via `finally { setIsAnalyzing(false) }`. No retry budget or rate limiting exists yet. Monitor real usage for repeated error-retry loops before deciding whether to add a retry counter, cooldown timer, or backend cost cap. Backend concern to gate at the API/billing layer? or also on the button? Precedent: Sprint 3 batch analysis already has per-session cost tracking that
could be extended. Status: Acceptable risk for MVP. Revisit after first real-user sessions.
- [ ] PhaseN: The jdOverrides state overlay pattern works but creates a brief window where context jds and overrides can disagree (between stream end and refreshSession resolving). This is harmless — the override data matches what the backend wrote — but a more robust pattern would be to optimistically update the context itself. Phase 1 if it causes issues.