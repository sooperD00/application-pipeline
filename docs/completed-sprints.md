# Completed Sprints — Phase 0

> Execution order: bottom-up (first sprint is at the bottom)

---

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