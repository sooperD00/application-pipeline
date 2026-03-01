# JD Pipeline Platform — Implementation Plan

## Vision

A tool that takes a job seeker from "600 LinkedIn results" to "6 tailored applications running in the background" in under 20 minutes — and learns what's working over time.

Built around a proven workflow. Opinionated defaults, editable prompts, and analytics that tell you where to focus.

## Stack

- **Backend**: FastAPI + Postgres (Railway) + SQLAlchemy/SQLModel
- **Frontend**: React (Vite)
- **LLM**: Claude API (Anthropic developer account)
- **Background jobs**: FastAPI `BackgroundTasks` initially, upgrade to `arq`/Redis if needed
- **Auth** (Phase 2+): anonymous sessions → magic link accounts

## Data Model (Core)

```
User
├── resumes[]              (up to 3, with user-assigned labels)
├── prompt_templates[]     (per-phase, versionable)
└── sessions[]
    ├── metadata           (board, filters, search_term, date)
    └── jds[]
        ├── raw_text
        ├── cleaned_text
        ├── company, role, employee_count, link
        ├── number           (position in session, maps to job board order)
        ├── status           (pending → apply/maybe/no, user-overridable)
        ├── analysis_text    (Claude's Phase 1 output)
        ├── app_questions    (optional, pasted by user)
        ├── cover_letter_requested  (boolean toggle)
        ├── additional_jd_text      (from application website)
        └── tailoring_jobs[]
            ├── status       (queued → processing → ready → reviewed)
            ├── resume_used  (FK to resume)
            ├── prompt_used  (snapshot)
            ├── output_resume_docx
            ├── output_cover_letter
            ├── output_app_answers
            └── chat_context (structured, for continuation)

ApplicationTracker (cross-session, persistent)
├── jd (FK)
├── stage          (application | phone_screen | interview_1 | interview_2 | offer | reject)
├── date
├── outcome        (pending | pass | fail)
├── notes
└── week_number    (derived, for goal tracking)
```

*(The tracker uses separate rows per stage, not one row updated over time — each stage is its own event with its own date and outcome.)*

---

## Phase 0 — "Replace My Excel Workflow"

**Goal**: Nicole can use this instead of Excel + manual Claude chats. Single user, deployed on Railway, functional end-to-end.

**What you get**: Paste JDs, get Apply/Maybe/No analysis with requirements breakdown, see results on fanned cards that sort themselves, kick off tailoring for Apply JDs.

### Backend (FastAPI + Postgres)

- `POST /sessions` — create session with metadata (board, filters, search_term)
- `POST /sessions/{id}/jds` — add a JD (auto-cleans text on ingest: strip empty lines, normalize whitespace, remove non-printable chars; store both raw and cleaned)
- `POST /sessions/{id}/analyze` — triggers Claude API batch analysis
  - Sends JDs in batches of 5 to Claude, using your proven prompt
  - Waits between batches (rate limiting + context management)
  - Stores analysis results and Apply/Maybe/No per JD
  - Returns results progressively (SSE or polling)
- `PATCH /jds/{id}/status` — user override of Apply/Maybe/No
- `POST /jds/{id}/tailoring` — kick off resume + cover letter generation
- `POST /jds/batch-tailor` — "Apply All" endpoint, queues up to 8
- `GET /sessions/{id}` — full session state for frontend
- Resume upload endpoints (up to 3, stored with labels)

### Frontend (React)

**Session View — Tab 1: Scrape & Analyze**

- Left panel: metadata fields (board, filters, search_term) — set once per session, sticky
- Right panel: large text input, "Add" button (or Enter)
- Above input: fanned cards, left-to-right, overlapping like a hand of playing cards
  - Each card shows: number, company name (truncated), role title
  - Cards start neutral (gray), animate to green/yellow/red as analysis returns
  - Apply cards drift left, No cards drift right, Maybe stays center
  - Click card number → expand in-place to show full JD
  - Status dropdown on each card (user can override)
- Progress indicator: "Analyzing batch 2 of 5..."

**Session View — Tab 2: Review & Audit (gray by default)**

- Vertical card layout for detailed reading
- Side-by-side: Claude's analysis vs. JD text
- "I disagree" feedback mechanism (for later prompt tuning)
- Skippable — most users won't need this

**Session View — Tab 3: Mini Tracker**

- Compact table of Apply JDs from this session
- Columns: number, company, role, status dropdown, app questions (click to paste), cover letter toggle, compare checkbox
- Shows matches from previous sessions: "You applied to Datadog on 2/14" banner at top
- Divider, then this week's applications, then this session's
- Row numbers visible (global count)
- "Compare" button (Phase 2 — grayed out for now)
- Link/button: "Open Full Tracker" → main nav

**Session View — Tab 4: Tailoring**

- "Apply All" button (uses JD + resume, no extras)
- Individual cards: click → popup modal for adding app questions, additional JD text, selecting resume version, then "Go"
- Each Apply JD gets a status box: queued → processing → ready for review
- Click "ready" → opens output view: tailored resume, cover letter, app answers
- Editable before export/download as docx
- "Continue for Interview Prep" button (appends structured context, opens new prompt)

**Main Nav — Full Tracker**

- All applications across all sessions
- Stage column: application, phone_screen, interview_1, etc.
- "Add Stage" button on a row → creates new entry with same company/role, new date, stage dropdown
- Week groupings with counts ("Week of 2/24: 8 applications, 2 phone screens")
- Running total visible ("Application #47")
- Status dropdowns, editable
- Filterable by metadata (search term, board, company size)

### Phase 0 Deliverables

1. FastAPI project scaffolding + SQLModel models + Postgres on Railway
2. Text cleaning utility (replaces your Excel macro)
3. Claude API integration with batched analysis (your prompt, hardcoded for now)
4. React app with Session Tab 1 (card UI + paste + analyze)
5. Resume upload
6. Session Tab 4 basics (tailoring with background tasks, output view)
7. Deploy to Railway

**What's deferred**: Tab 2 audit view, Tab 3 mini tracker, full tracker, compare, analytics, multi-user, payments. You use it, your brother uses it, you iterate.

---

## Phase 1 — "My Brother Can Use It Too"

**Goal**: Two real users. Persistence, the tracker, and the session flow polished enough that someone who isn't Nicole can follow it.

### Additions

- **Anonymous sessions with 7-day persistence** — cookie-based session token, server stores data, nudge to create account
- **Account creation** — email + magic link (no password), converts anonymous session data
- **Mini tracker (Tab 3)** — the compact command center table with app questions, cover letter toggle, status dropdowns
- **Full tracker on main nav** — cross-session, stage tracking, week groupings, row counts
- **Company matching** — when new session results come in, flag companies that appear in previous sessions
- **Prompt as a visible, read-only panel** — user can see what prompt is being sent in each phase (editing comes in Phase 2)
- **Onboarding flow** — brief "here's how this works" for first-time users

---

## Phase 2 — "It's a Product"

**Goal**: The compare feature, prompt editing, and the review tab. Feature-complete for the LinkedIn blog post.

### Additions

- **Compare tab** — checkbox-select JDs from mini tracker, up to 5, opens new tab with Claude comparison using editable prompt
- **Review & Audit tab (Tab 2)** — vertical detail view, side-by-side analysis, "I disagree" capture
- **Prompt editor** — per-phase prompt templates with variable slots (`{jd_text}`, `{resume}`, `{metadata}`), version history, save/restore, user can fork defaults
- **Interview stage tracking** — separate rows per stage in full tracker, with dates and outcomes
- **Chat context continuation** — "Continue for Interview Prep" carries structured context (JD + analysis + tailored resume + app questions) into new Claude conversation
- **Export** — download tracker as CSV/Excel for people who still want their spreadsheet

---

## Phase 3 — "People Pay For This"

**Goal**: Analytics dashboard and monetization. The funnel metrics that make the blog post compelling.

### Additions

- **Funnel analytics dashboard**
  - Session → Apply → Application Submitted → Phone Screen → Interview → Offer
  - Conversion rates at each stage
  - Breakdown by metadata: which search terms produce the most Applies? Which boards? Which company sizes?
  - Time-series: applications per week vs. target
  - Hit rate: callbacks per application, segmented by search term and resume version
- **Free tier**: 1 session (25 JDs), no account required, 7-day data persistence
- **Paid tiers**:
  - 10 sessions — one-time purchase (the "I'm actively searching" package)
  - 50 sessions — discounted (the "this is going to take a while" package)
  - Monthly subscription — uncapped sessions with some per-session Apply cap (~8 tailoring jobs per session to control API costs)
- **Payment integration** — Stripe, minimal
- **Usage tracking** — sessions consumed, API cost per user (internal metric)

---

## Phase 4 — "Polish and Grow"

- Resume analysis features (which resume version performs best for which JD types)
- Prompt marketplace (users share effective prompts)
- Additional job board-specific metadata templates
- Mobile-responsive UI
- Interview prep document generation (structured phase with its own prompts)
- Thank-you note generation post-interview
- "Referred by" tracking (for networking-sourced applications)
- Strategic advice aggregation (Claude's cross-JD observations surfaced in analytics: "you keep getting matched on Flink — develop this further")

---

## Implementation Notes

### Claude API Integration Pattern

The platform manages Claude conversations, not raw API calls. Each phase has a conversation context:

```
Phase 1 (Batch Analysis):
  - 1 conversation per session
  - JDs sent in batches of 5
  - Platform waits, meters, collects results
  - Full cross-JD context maintained (this is the big win over manual 5-at-a-time)

Phase 4 (Tailoring):
  - 1 conversation per Apply JD
  - Context: JD + metadata + selected resume + analysis from Phase 1 + app questions (if provided)
  - Output: structured (resume text, cover letter text, app answers as separate fields)
  - Conversation persisted for continuation (interview prep, thank you notes)
```

### The Free Trial Technical Flow

1. User lands on site, no account
2. Server creates anonymous session (cookie + server-side token)
3. User uploads resume, creates session, pastes JDs — all stored server-side
4. After 25 JDs analyzed: "Nice! To save your results and keep going, create an account (just an email)."
5. Data persists 7 days without account, permanently with account
6. Second session attempt without account → "Create an account to start a new session" (this is the conversion point)

### Card UI Behavior

```
Initial state:    [1][2][3][4][5]...[25]  (gray, fanned left-to-right)

During analysis:  [1✓][2✓][3?][4][5]...[25]  (first batch coloring in)

After analysis:   [3][7][12][15]  |  [8][19]  |  [1][2][4][5][6][9]...
                   ^^^ Apply ^^^    ^^ Maybe ^^   ^^^^^^^ No ^^^^^^^
                   (green, left)   (yellow, mid)  (red, right, smaller)
```

Cards animate to their positions as results arrive. The Apply cluster is visually prominent. No cards are prominent.

### Cost Estimation

- Claude API (Sonnet for batch analysis, Sonnet for tailoring): ~$0.01–0.03 per JD analyzed, ~$0.05–0.15 per tailoring job
- Per session (25 JDs, 4 Apply tailored, 1 interview): ~$0.50–1.50 in API costs
- Railway (Postgres + app): ~$5–10/month at low scale
- Pricing floor for paid sessions: $3–5 per session to maintain healthy margin


*(These are rough estimates — track actual costs from day one.)*
