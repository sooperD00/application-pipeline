# ApplicationPipeline

**Job application orchestration for humans.**

Takes you from 600 LinkedIn results to 6 tailored applications running in the background — in under 20 minutes. Then tells you what's working so you can do it better next week.

## What It Does

You paste job descriptions. The platform analyzes them against your resume, recommends which ones are worth your time, and generates tailored resumes and cover letters for the winners — in parallel, while you go do something else.

Built around a real workflow that increased callback rates during a real job search. Opinionated defaults, editable prompts, and funnel analytics that show you where to focus.

## The Funnel

```
600 job board results
 → 25 scraped JDs (manual, ~2 min)
  → 6 Apply recommendations (AI analysis, ~5 min)
   → 6 tailored applications (background generation, ~10 min)
    → track → interview → offer
```

## Stack

| Layer | Tech |
|-------|------|
| Backend | FastAPI + SQLModel + Postgres (Railway) |
| Frontend | React (Vite) |
| LLM | Claude API (Anthropic) |
| Background Jobs | FastAPI BackgroundTasks → arq/Redis |
| Auth | Anonymous sessions → magic link accounts |

## Status

🟡 **Phase 0 — In Development**

Building the core single-user flow: paste JDs, get analysis, kick off tailoring. See [docs/implementation-plan.md](docs/implementation-plan.md) for the full roadmap.

## Quick Start

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

Requires a `.env` with `ANTHROPIC_API_KEY` and `DATABASE_PUBLIC_URL`.

## Docs

- [Implementation Plan](docs/implementation-plan.md) — phased build roadmap
- [Architecture](docs/architecture.md) — data model, API contracts, integration patterns
- [Workflow](docs/workflow.md) — the human method this automates
- [Decisions](docs/decisions.md) — architecture decision records
- [Service Layer Notes](docs/service-layer-notes.md) — implementation TODOs and design notes
- [Completed Sprints](docs/completed-sprints.md) — what shipped and when
- [Remaining Sprints](docs/remaining-sprints.md) — what's next (Phase 0)
- [Original Prompts](docs/original-prompts.md) — the manual Claude prompts this automates

## Repo Structure

> `[x]` = implemented and on disk. `[ ]` = planned — the file doesn't exist yet but its location is part of the design. This tree is both a map and a roadmap.

```
ApplicationPipeline/
├── README.md
├── backend/
│   ├── tests/                       # - [x]  71/71 pass
│   │   ├── conftest.py
│   │   ├── test_resumes.py
│   │   ├── test_sessions.py
│   │   ├── test_tailoring.py
│   │   └── test_text_cleaning.py
│   └── pyproject.toml               # - [x] Python project manifest (replacing setup.[py|cfg])
│   ├── scripts/
│   │   ├── __init__.py
│   │   ├── seed.py                  # - [x] Seed 3 real resumes, 7 real JDs (test mod 5 batches)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # - [x] FastAPI app, CORS, lifespan
│   │   ├── config.py                # - [x] settings, limits, model defaults
│   │   ├── database.py              # - [x] engine, session factory
│   │   ├── models.py                # - [x] SQLModel entities (7 tables)
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── sessions.py          # - [x] session CRUD (POST, POST/jds, GET)
│   │   │   |                        # - [x] batch analyze SSE (POST /{id}/analyze)
│   │   │   |                        # - [x] batch-tailor (POST /{id}/batch-tailor)
│   │   │   ├── jds.py               # - [x] JD CRUD, status overrides, enrichment
│   │   │   |                        # - [x] single tailor, status, outputs, docx download
│   │   │   ├── resumes.py           # - [x] paste, edit, list, delete (max 3)
│   │   │   └── activities.py        # - [ ] active list, add/complete, tracker view
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── claude.py            # - [x] API client, prompt assembly, response parsing
│   │   │   ├── analysis.py          # - [x] batch analysis (batches of 5, meta-summary)
│   │   │   ├── tailoring.py         # - [x] parallel tailoring (semaphore), docx handling
│   │   │   ├── docx_builder.py      # - [x] dumb renderer: Claude JSON → python-docx (ADR-011)
│   │   │   ├── activities.py        # - [ ] cascade templates, schedule_activities()
│   │   │   └── text_cleaning.py     # - [x] JD ingest pipeline (strip, normalize, collapse)
│   │   └── prompts/
│   │       ├── analysis.txt         # - [ ] system default: analysis phase
│   │       ├── resume_generation.txt # - [ ] system default: resume + docx formatting
│   │       └── cover_letter.txt     # - [ ] system default: cover letter + app answers
│   ├── alembic/
│   │   ├── env.py                   # - [x] 
│   │   └── versions/                # - [x] migration scripts
│   ├── alembic.ini                  # - [x] boilerplate
│   ├── requirements.txt
│   ├── .env.example                 # - [x] example
│   └── .env                         # - [x] ANTHROPIC_API_KEY, DATABASE_PUBLIC_URL
├── frontend/
│   ├── src/
│   │   ├── App.jsx                     # - [x] nav bar (ADR-015) + nested routes (react-router-dom v7)
│   │   ├── __tests__/
│   │   │   ├── App.test.jsx            # - [x] shell/routing tests (all static)
│   │   │   ├── JDCard.test.jsx         # - [x] component test: card renders props, no API awareness
│   │   │   ├── SessionDetailPage.test.jsx # - [x] integration: session fetch, JD paste flow, card grid
│   │   │   ├── CardFan.test.jsx        # - [ ] fanned layout tests (once CardFan container exists)
│   │   ├── pages/
│   │   │   ├── CalibratePage.jsx       # - [x] stub (session-scoped)
│   │   │   ├── NotFoundPage.jsx        # - [x] 404 catch-all
│   │   │   ├── ResumesPage.jsx         # - [x] stub (global)
│   │   │   ├── ReviewPage.jsx          # - [x] stub (session-scoped)
│   │   │   ├── SessionDetailPage.jsx   # - [x] Tab 1: JD paste form + card grid
│   │   │   ├── SessionLayout.jsx       # - [x] useParams → fetch session → Outlet context
│   │   │   ├── SessionsPage.jsx        # - [x] session list + create form
│   │   │   ├── TailoringPage.jsx       # - [x] stub (session-scoped)
│   │   ├── main.jsx                    # - [x] BrowserRouter entry point
│   │   ├── index.css                   # - [x] Tailwind v4 @import + @theme (custom pipeline-* palette)
│   │   ├── test-setup.js               # - [x] Vitest setup (jest-dom matchers)
│   │   ├── components/
│   │   │   ├── JDCard.jsx              # - [x] single JD card (number, company, role, status color)
│   │   │   ├── JDPasteForm.jsx         # - [x] text area + company/role fields, submit
│   │   │   ├── SessionCreateForm.jsx   # - [x] board, filters, search_term
│   │   │   ├── CardFan.jsx             # - [ ] Tab 1: fanned card layout, color-coded sort
│   │   │   ├── MetaAnalysis.jsx        # - [ ] Tab 1: Claude's rolling summary panel
│   │   │   ├── TailoringStatus.jsx     # - [ ] Tab 4: status boxes, output viewer
│   │   │   └── ActiveList.jsx          # - [ ] Active Applications: to-do by due date
│   │   ├── hooks/
│   │   │   └── useSSE.js               # - [ ] SSE consumption for batch analysis
│   │   └── api/
│   │       └── client.js               # - [x] fetch wrappers for backend routes
│   ├── index.html                      # - [x] 
│   ├── vite.config.js                  # - [x] dev proxy (/api, /health → FastAPI), Vitest config
│   ├── eslint.config.js                # - [x]
│   └── package.json                    # - [x] React 19, Tailwind v4, Vitest
├── docs/
│   ├── architecture.md
│   ├── completed-sprints.md
│   ├── decisions.md
│   ├── implementation-plan.md
│   ├── original-prompts.md
│   ├── remaining-sprints.md
│   ├── service-layer-notes.md
│   └── workflow.md
└── LICENSE                          # BSL 1.1 → Apache 2.0 (2029-03-01)
```

## License

Licensed under the Business Source License 1.1 — see [LICENSE](LICENSE).
Converts to Apache 2.0 on 2029-03-01.
