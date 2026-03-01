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

## License

Licensed under the Business Source License 1.1 — see [LICENSE](LICENSE).
Converts to Apache 2.0 on 2029-03-01.
