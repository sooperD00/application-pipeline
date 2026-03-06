# Remaining Sprints — Phase 0

> Execution order: bottom-up. Next sprint is at the bottom.

---

Sprint 11 — Tests
Audit test coverage, fill gaps. Priority: test_analysis.py (batching logic, error/retry with mocked Claude client), then anything needed for multi-user safety in Phase 1.

Sprint 10 — Deploy to Railway
Environment variables, Alembic migration on prod DB, CORS for prod domain. Half-session if nothing is on fire.

Sprint 9 — Frontend Tab 4
Tailoring kickoff UI per JD. Status polling (queued → processing → ready). Output view: resume text, cover letter, app answers. Download button.

Sprint 8 — Frontend Tab 1: SSE + Cards
SSE consumer hook. Cards animating green/yellow/red in real time as analysis returns. Meta-analysis panel. The "show a non-engineer" moment.

Sprint 7 — Frontend Tab 1: Session + JD Flow
Stand up the React app for real (routing, API client wiring). Session creation form. JD paste flow with card display. Done when you can create a session and paste JDs through the UI.

Sprint 6 — Backend Catchup
- `GET /api/sessions` — list all sessions for current user (session picker prerequisite)
- `GET /api/sessions/{id}/tailoring-jobs` — batch status dashboard (Tab 4 prerequisite)
- `GET /api/jds/{id}/tailoring` — per-JD tailoring history (Tab 4 prerequisite)
- Batch-tailor: skip JDs that already have a completed tailoring job unless `force=true`
- One targeted integration test for the tailoring pipeline (prompt assembly → Claude mock → docx_builder → valid docx bytes). Silent failures here are harder to catch by eye than a bad SSE stream.