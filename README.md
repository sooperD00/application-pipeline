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

Requires a `.env` with `ANTHROPIC_API_KEY` and `DATABASE_URL`.

## Docs

- [Implementation Plan](docs/implementation-plan.md) — phased build roadmap
- [Architecture](docs/architecture.md) — data model, API contracts, integration patterns
- [Workflow](docs/workflow.md) — the human method this automates
- [Decisions](docs/decisions.md) — architecture decision records

## Repo Structure

```
ApplicationPipeline/
├── README.md
├── backend/
│   ├── tests/
│   │   ├── test_text_cleaning.py    # - [x] 27 passes!
│   │   └── test_sessions.py         # - [-] 9 skips (expected until next phase)
│   └── pyproject.toml               # - [x] Python project manifest (replacing setup.[py|cfg])
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # - [x] FastAPI app, CORS, lifespan
│   │   ├── config.py                # - [x] settings, limits, model defaults
│   │   ├── database.py              # - [x] engine, session factory
│   │   ├── models.py                # - [x] SQLModel entities (7 tables)
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── sessions.py          # - [x] session CRUD, batch analyze (SSE)
│   │   │   ├── jds.py               # - [ ] JD CRUD, status overrides, enrichment
│   │   │   ├── resumes.py           # - [ ] paste, edit, list, delete (max 3)
│   │   │   ├── tailoring.py         # - [ ] single + batch-tailor, status, outputs
│   │   │   └── activities.py        # - [ ] active list, add/complete, tracker view
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── claude.py            # - [ ] API client, prompt assembly, response parsing
│   │   │   ├── analysis.py          # - [ ] batch analysis (batches of 5, meta-summary)
│   │   │   ├── tailoring.py         # - [ ] parallel tailoring (semaphore), docx handling
│   │   │   ├── activities.py        # - [ ] cascade templates, schedule_activities()
│   │   │   └── text_cleaning.py     # - [x] JD ingest pipeline (strip, normalize, collapse)
│   │   └── prompts/
│   │       ├── analysis.txt         # - [ ] system default: analysis phase
│   │       ├── resume_generation.txt # - [ ] system default: resume + docx formatting
│   │       └── cover_letter.txt     # - [ ] system default: cover letter + app answers
│   ├── alembic/
│   │   ├── env.py                   # - [x] 
│   │   └── versions/                # - [x] migration scripts
│   ├── alembic.ini                  # - [x] 
│   ├── requirements.txt
│   ├── .env.example                 # - [x] example
│   └── .env                         # - [x] ANTHROPIC_API_KEY, DATABASE_PUBLIC_URL
├── frontend/
│   ├── src/
│   │   ├── App.jsx                  # - [ ] 
│   │   ├── main.jsx                 # - [ ] 
│   │   ├── components/
│   │   │   ├── CardFan.jsx          # - [ ] Tab 1: fanned JD cards, color-coded
│   │   │   ├── MetaAnalysis.jsx     # - [ ] Tab 1: Claude's rolling summary panel
│   │   │   ├── TailoringStatus.jsx  # - [ ] Tab 4: status boxes, output viewer
│   │   │   └── ActiveList.jsx       # - [ ] Active Applications: to-do by due date
│   │   ├── hooks/
│   │   │   └── useSSE.js            # - [ ] SSE consumption for batch analysis
│   │   └── api/
│   │       └── client.js            # - [ ] fetch wrappers for backend routes
│   ├── index.html                   # - [ ] 
│   ├── vite.config.js               # - [ ] 
│   └── package.json                 # - [ ] 
├── docs/
│   ├── architecture.md
│   ├── decisions.md
│   ├── implementation-plan.md
│   ├── workflow.md
│   └── service-layer-notes.md
└── LICENSE                          # BSL 1.1 → Apache 2.0 (2029-03-01)
```

## License

Licensed under the Business Source License 1.1 — see [LICENSE](LICENSE).
Converts to Apache 2.0 on 2029-03-01.
