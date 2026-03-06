# Implementation Plan

## Vision

A tool that takes a job seeker from "600 LinkedIn results" to "6 tailored applications running in the background" in under 20 minutes — and learns what's working over time.

Built around a proven workflow. Opinionated defaults, editable prompts, and analytics that tell you where to focus.

## Stack

- **Backend**: FastAPI + Postgres (Railway) + SQLModel
- **Frontend**: React (Vite)
- **LLM**: Claude API (Anthropic) — Opus 4.6 by default, configurable per call
- **Background jobs**: FastAPI `BackgroundTasks` initially, upgrade to `arq`/Redis if needed
- **Auth** (Phase 2+): anonymous sessions → magic link accounts

## Data Model

See [architecture.md](architecture.md) for full SQLModel entity definitions.

**Entities** (each is its own SQLModel table with explicit foreign keys):

- **User** — account info, auth token
- **Resume** — up to 3 per user, labeled (e.g. "Technical", "Leadership"), text-only for Phase 0 (paste and edit in-app)
- **PromptTemplate** — per-phase, per-user, versionable, forkable from defaults. Phases: `analysis`, `resume_generation`, `cover_letter`, `app_answers` (composable tailoring pieces assembled into one call; `cover_letter` and `app_answers` toggled independently per JD — ADR-012), plus `calibrate`, `compare`, `interview_prep` (standalone)
- **Session** — one metadata set (board, filters, search_term), one batch of up to 25 JDs
- **JD** — belongs to a Session; holds raw/cleaned text, company, role, compensation, employee_count, link, status, analysis results, app questions, additional JD text, cover letter toggle
- **TailoringJob** — belongs to a JD (not a Session); holds status, resume used, prompt snapshot, outputs (resume docx, cover letter, app answers), chat context for continuation
- **Activity** — belongs to a JD; a to-do that happened (or hasn't yet). Pipeline stages (`application`, `phone_screen`, `interview_1` through `interview_7`, `offer`, `reject`) and action items (`follow_up`, `prep_doc`, `prep_time`, `thank_you`, `post_mortem`) live in the same table. `completed_at IS NULL` = still on your to-do list.

Key relationships:
- User → Sessions (one-to-many)
- User → Resumes (one-to-many, max 3)
- User → PromptTemplates (one-to-many)
- Session → JDs (one-to-many)
- JD → TailoringJobs (one-to-many)
- JD → Activities (one-to-many, the stage chain + action items)

---

## Phase 0 — "Replace My Excel Workflow"

**Goal**: A working tool for 1-2 users. Paste JDs, get analysis, kick off tailoring. Deployed on Railway.

### Backend

- `POST /sessions` — create session with metadata
- `POST /sessions/{id}/jds` — add JD (auto-clean on ingest, store raw + cleaned)
- `POST /sessions/{id}/analyze` — batch analysis via Claude API
  - Batches of 5, full conversation context maintained across batches
  - Returns results progressively (SSE)
  - Includes meta-analysis summary after each batch (cross-JD strategic observations)
- `PATCH /jds/{id}` — update status (user override), app questions, additional JD text, cover letter toggle, compensation
- `POST /jds/{id}/tailoring` — kick off single tailoring job
- `POST /sessions/{id}/batch-tailor` — "Apply All", runs up to 4 in parallel (`asyncio.gather`), configurable cap
- `GET /sessions/{id}` — full session state
- `GET /jds/{id}/tailoring/{job_id}` — tailoring job status + outputs
- Resume CRUD (paste, label, edit, list, delete; max 3)
- Activities: `GET /api/activities/active` (open to-dos by due date), `POST /api/activities` (log stage, triggers cascade)

### Frontend — Session View

**Tab 1: Scrape & Analyze**

Top strip: metadata fields (board, filters, search_term) — set once per session, read-only after first JD added.

Main area: fanned cards, left-to-right, overlapping like a hand of cards.
- Each card: number, company (truncated), role (truncated)
- Start gray, animate to green (Apply) / yellow (Maybe) / red (No) as analysis returns
- Apply drifts left, No drifts right, Maybe stays center
- Click card → modal popup showing full JD text (doesn't displace the card view)
- Status dropdown on each card for overrides
- Spinner/pulse on the 5 cards currently being analyzed, checkmark when done

Left panel (below metadata): Claude's rolling meta-analysis summary. Updates after each batch of 5. This is the strategic advice layer — search term suggestions, skill gap observations, "apply to these 3 then finish your Flink project" type guidance.

**Tab 2: Calibrate (gray, skipped by default)**

For when the user wants to push back on results or recalibrate.
- Loads JDs that user flagged for review (checkbox on cards in Tab 1 or rows in Tab 3)
- Can also load Claude's meta-analysis summary from Tab 1
- Free-form Claude conversation with full context (the flagged JD + resume used)
- Editable prompt box — user can modify and save versions
- User can update JD status from here and kick back to Tab 3
- Description text for new users: "Use this to test Claude's judgment against your own, recalibrate your resume selection, or explore whether a Maybe is actually an Apply."

**Tab 3: Review & Enrich**

Left side — compact table:
- Columns: global row #, status (dropdown), company, role, compensation, app questions (click to paste), cover letter (toggle), compare (checkbox, grayed Phase 2), flag for review (checkbox → sends to Tab 2)
- Section 1: Previous session matches (companies matching current Apply set, like an Excel filter)
- Divider
- Section 2: No and Maybe JDs — grayed, collapsed, expandable (Gmail-style)
- Divider
- Section 3: This week's completed/in-progress applications
- Divider
- Section 4: Apply JDs from this session — full interactive rows, click cells to enrich
- Link/button: "Open Full Tracker" → main nav

**Tab 4: Tailoring**

- "Apply All" button — uses JD + selected resume, no extras, kicks off up to 4 in parallel
- Individual: click a JD → popup modal to add app questions, additional JD text, select resume version → "Go"
- Status boxes per JD: queued → processing → ready for review
- Click "ready" → output view: tailored resume, cover letter, app question answers
- Editable before export/download as docx
- "Continue for Interview Prep" button (1 free for unpaid users — show this on the button itself)
- Interview prep also accessible later from Full Tracker

**Main Nav — Full Tracker**

- All applications across all sessions
- Stage column: application → phone_screen → interview_1 through interview_7 → offer/reject
- "Add Stage" button → new Activity row, same JD, new date, stage dropdown (triggers action item cascade)
- Week groupings with counts
- Running total visible
- Status dropdowns, editable
- Filterable by metadata
- Interview prep button per row (context carried forward)

### Phase 0 Deliverables

1. FastAPI project: SQLModel entities, Alembic migrations, Postgres on Railway
2. Text cleaning utility
3. Claude API integration: batched analysis with meta-summary, parallel tailoring
4. React app: Tab 1 (card UI + analyze), Tab 4 (tailoring + output review)
5. Resume paste & edit (text-only)
6. Deploy to Railway

**Deferred**: Tab 2 Calibrate, Tab 3 Review & Enrich, Full Tracker, compare, analytics, multi-user, auth, payments.

---

## Phase 1 — "My Brother Can Use It Too"

**Goal**: Two users. Persistence, tracker, and flow polished for someone who didn't design it.

- Anonymous sessions with 7-day server-side persistence (cookie token, nudge to create account)
- Account creation: email + magic link, converts anonymous data
- Tab 3: Review & Enrich table with all sections
- Full Tracker on main nav with stage tracking and week groupings
- Company matching across sessions
- Prompt templates visible (read-only) per phase
- Onboarding flow for first-time users

---

## Phase 2 — "It's a Product"

**Goal**: Feature-complete for the LinkedIn blog post.

- Tab 2: Calibrate — fully functional with flagged JD loading, free-form Claude chat, prompt editing
- Compare: checkbox-select from Tab 3, up to 5 JDs, dedicated tab with editable prompt
- Prompt editor: per-phase templates, variable slots, version history, fork from defaults
- Chat context continuation for interview prep
- Export tracker as CSV/Excel
- Interview prep and thank-you note generation (Tab 5, with prompt template)

---

## Phase 3 — "People Pay For This"

**Goal**: Analytics and monetization.

- Funnel analytics dashboard (session → apply → submitted → phone screen → interview → offer, broken down by metadata)
- Time-series: applications per week vs. target, hit rate by search term and resume version
- Free tier: 1 session (25 JDs), 4 parallel tailoring jobs, 1 interview prep, no account required, 7-day persistence
- Paid tiers:
  - 10 sessions pack
  - 50 sessions pack (discounted)
  - Monthly subscription: uncapped sessions, 8 parallel tailoring jobs, uncapped interview preps
- Stripe integration
- Cost tracking per user (internal)

---

## Phase 4 — "Polish and Grow"

- Resume analysis (which version performs best for which JD types)
- Resume binary uploader: accepts docx/pdf, analyzes formatting, feeds style preferences into generation prompt
- Prompt marketplace (users share prompts)
- Job board-specific metadata templates
- Mobile-responsive
- "Referred by" tracking
- Strategic advice aggregation (Claude's cross-session observations surfaced in analytics)
- User-selectable model tier (Opus vs Sonnet, pay more for Opus)

---

## Claude API Integration

```
Batch Analysis (1 conversation per session):
  - JDs sent in batches of 5
  - Meta-analysis summary updated after each batch
  - Full cross-JD context maintained
  - Model: claude-opus-4-6 (configurable)

Tailoring (1 conversation per Apply JD, up to 4 parallel):
  - Context: JD + metadata + resume + Phase 1 analysis + app questions
  - Prompt assembled from composable templates: analysis + resume_generation
    + cover_letter (if requested) + app_answers (if app questions provided)
  - Output: structured (resume docx, cover letter, app answers as separate fields)
  - output_resume is extracted from the docx for in-app display — not input to it
  - Conversation persisted for interview prep continuation
  - Model: claude-opus-4-6 (configurable)

Calibrate (1 conversation per flagged JD or meta-summary):
  - Context: flagged JD(s) + resume + user's prompt
  - Free-form, user-directed
  - Model: claude-opus-4-6 (configurable)
```

## Free Trial Flow

1. User lands, no account. Server creates anonymous session (cookie + server token).
2. User pastes resume, creates session, pastes JDs — stored server-side.
3. Full session runs: analysis, review, tailoring (up to 4 parallel), 1 interview prep.
4. "Save your results and start a new session — just enter your email."
5. Data persists 7 days without account, permanently with account.
6. Second session attempt without account → conversion point.

## Cost

- Model: Opus 4.6 (highest quality, higher cost — acceptable if margins work)
- Estimated per session (25 JDs analyzed, 6 tailored): TBD after real testing
- Railway (Postgres + app): ~$5-10/month at low scale
- Track actual API costs from day one with observability logging
- Price sessions to maintain margin after real cost data is in
