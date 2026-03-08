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

Consider if any of this housekeeping will fit in this sprint context and add it if it will:
- [ ] datetime.utcnow() deprecation warnings — switch to datetime.now(datetime.UTC) across models.py and tailoring.py (housekeeping, any sprint)
- [ ] HTTP_422_UNPROCESSABLE_ENTITY deprecation — FastAPI renamed to HTTP_422_UNPROCESSABLE_CONTENT (housekeeping, any sprint)
- [ ] batch-tailor skip logic doesn't account for processing/queued jobs (could create duplicates if you double-click "Apply All" fast) — Sprint 9 when Tab 4 UI makes this a real concern
- [ ] timestamps are showing up 1 day ahead of what day it actually is. Today is 3/7/2026 in Oregon. Swagger output gives: "created_at": "2026-03-08T00:25:15.133465", "completed_at": "2026-03-08T00:26:21.237301". Not important for MVP (Nicole is only user).
