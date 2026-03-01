# JD Pipeline Platform — Implementation Plan

<---
feedback: on the name
need to communicate: pipeline + strategy + automation
It saves time and increases signal
It learns and optimizes over time
clarity > cleverness

1. Ultra-Clear, Functional Names (High Signal)
ApplyPipeline
Repo: apply-pipeline

ApplicationPipeline
Repo: application-pipeline

JobPipeline
Repo: job-pipeline

ApplicationEngine
Repo: application-engine

TailoredApply
Repo: tailored-apply

ApplyFlow
Repo: apply-flow

2. Strategic / Optimization Angle

OfferFunnel
Repo: offer-funnel

ApplicationFunnel
Repo: application-funnel

InterviewFunnel
Repo: interview-funnel

SignalApply
Repo: signal-apply

ConversionApply
Repo: conversion-apply

PipelineIQ
Repo: pipeline-iq

3. Automation / Parallelization Angle
AutoApply Studio
Repo: autoapply-studio

ParallelApply
Repo: parallel-apply

ApplyBatch
Repo: apply-batch

ApplyOrchestrator
Repo: apply-orchestrator

JD Orchestrator
Repo: jd-orchestrator

4. Strong, Memorable, Product-Ready
ApplyForge
Repo: apply-forge

OfferForge
Repo: offer-forge

PipelineForge
Repo: pipeline-forge

ApplyCraft
Repo: apply-craft

InterviewOS
Repo: interview-os

ApplicationOS
Repo: application-os

5. ones I like:
ApplicationPipeline  <--
ApplyOrchestrator <--
ApplicationOS
OfferFunnel
PipelineForge

--->

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


<---
feedback: 
1. definitely need compensation in the jds[]
2. what are the pros/cons of keeping everything under User like that? I assumed multiple entities in the data model but I'm not sure what your indentations meen exactly in terms of the different entities and how that would shake out, because I'd prbably not store tailoring_jobs[] under session... I don't think of them as belonging to a session in my personal work... but maybe that needs to be the case to track limits etc? or maybe you are just maping out the data model in a way I'm not used to since I"m used to seeing different entities and the FK labeled and the infrastructure layer kind of separate, which SQLModel doesn't quite do - can you help me out here? I'm open to different ways of doing this that make sense and can be maintained easily by me.
3. you need up to 7 interview slots like up to interview_7 because some chains are long. that should be sufficient and keep things simple as an enum which is what it looks like you're leaning towards
-->

---

## Phase 0 — "Replace My Excel Workflow"

**Goal**: Nicole can use this instead of Excel + manual Claude chats. Single user, deployed on Railway, functional end-to-end.

**What you get**: Paste JDs, get Apply/Maybe/No analysis with requirements breakdown, see results on fanned cards that sort themselves, kick off tailoring for Apply JDs.

<---
feedback:
hmmm I'm reading the "replace my excel workflow" section and I realize that I have not designed a place for the user to really *read* the output of the initial comparison analysis with the requirements breakdown and the text. I usually don't care too much about reading it myself now bc I've already seen you be incredibly accurate, but a new user will need to read it to reassure themselves and to tweak things if they dont' really match what's expected. Where should this go? Maybe in that "review" tab where they can click on those vertical cards. That makes sense. But what about this... what if the mini-summary is where they review - I think that makes more sense. They don't need vertical cards. They have a verticle structure to click on in this table. The maybe and no can be color coded and collapsed here too and faded, and they can review/expand or not exactly like you do in gmail. I think that's better. I think there should be a tab "argue with claude" but I haven't designed it yet... that's what should be gray... a gray tab in between phase 0 and phase 1 where you recalibrate with claude - maybe resume isn't quite right. maybe search terms aren't right. I'll have to think about designing prompt help for that phase, but I think we should include it as gray and some description of what the user should do in that phase. They should be able to kick 1 JD analysis in there and chat with claude about it in a fresh context... does that make sense? Mabye they can also kick claude's overall summary from phase 0 into there and chat with claude about it as well. This is very doable I think, though the user for now will have to decide what the deliverable is.
--->

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
<---
feedback:
is this gonna be done in series or parallel? part of the time savings power is the parallel here - that's the difference between take a bathroom/water break and come back in an hour... I want parallel...I'd rather have 4 in parallel and maybe that's a reasonable "free tier" number, with subscribers can go to 8?
--->
- `GET /sessions/{id}` — full session state for frontend
- Resume upload endpoints (up to 3, stored with labels)

### Frontend (React)

**Session View — Tab 1: Scrape & Analyze**

- Left panel <--top-->: metadata fields (board, filters, search_term) — set once per session, sticky
<---
- Left panel bottom: claude's meta analysis, replaced after each batch of 5 - you usually give me a summary summarizing all JDs analyzed thus far in a paragraph or so, and we could add info to the prompt to ensure we get this response every time and have him structure it in a tagged section for us (the one where he talks about "you haven't had a lot of hits on this search term - try xyz instead" or "your most consistent skill gap is flink - the best thing you could do is apply to JDs 1,2,3 and then finish your flink project rather than go for 10 this week. Then next week you could easily do 20 with a much higher call back rate.")
--->
- Right panel: large text input, "Add" button (or Enter)
- Above input: fanned cards, left-to-right, overlapping like a hand of playing cards (but not fanned)
  - Each card shows: number, company name (truncated), role title (truncated)
  - Cards start neutral (gray), animate to green/yellow/red as analysis returns
  - Apply cards drift left, No cards drift right, Maybe stays center
  - Click card number → expand in-place to show full JD - is this better on the right-hand side? it might be better to expand this on left hand side or as a modal popup since I wouldn't want to lose my visual stickiness sense of my main dashboard work area... I think a modal popup because i want the serious review against claude's analysis to be on the next tab anyway... what do you think? Here I just want to sort and get a handle on what you have (4 applies, 6 maybes, ok to go to next phase and have some confidence since this took 2 min of scraping and 5 min of claude analyzing, read the overall analysis on the left and move forward or not... but I'm not sure...). Do you think review belongs here or in next tab or both?
  - Status dropdown on each card (user can override) - I kinda want the user to do these activities on the review tab with the session+prev matches spreadsheet...
- Progress indicator: "Analyzing batch 2 of 5..." - this might not be necessary because you see the sorting occuring, but something small is nice. honestly I'd like a spinny or other mark on the 5 cards he's analyzing if that's what he's doing and a done or ready indication on the button they click to analyze or something... waht do you think?

**Session View — Tab 2: Review & Audit (gray by default)**

- Vertical card layout for detailed reading
- Side-by-side: Claude's analysis vs. JD text
- "I disagree" feedback mechanism (for later prompt tuning)
- Skippable — most users won't need this

<---
let's change this to Calibrate and use the design from above - the pull ins of the summary analysis or 1 JD analysis plus the resume used for it and a conversation with claude - free form for now, I'll write a prompt later. There should be a prompt box for this tab that users can edit and save versions of, same as the others. The flow would be by default this is skipped, but there to remind you if you want to go back.
--->

**Session View — Tab 3: Mini Tracker / Review / Enrichment**
on the left:
- Compact table of <---
  - Columns: row number (global JD count), status, date, session (number? metadata?), batch number, number, company, role, status dropdown, app questions (click to paste), cover letter toggle, date, compare checkbox
  - rows from the merged all sessions tracker table that match current JDs (like an excel filter on if you included matching companies to the current apply group)
  - Divider
  - no and maybe JDs grayed out but expandable (do you agree?)
  - Divider
  - then this week's DONE or IP applications
  - Divider
  - Apply JDs from this session in visible rows where you can click in the cells to enrich the data
- "Compare" button (Phase 2 — grayed out for now)
- Link/button: "Open Full Tracker" → main nav
- this is a busy tab... I'm not sure JD review belongs here now that I'm adding stuff. I think the user should be able to kick a JD to the previous "review/calibrate" tab with a button from the row, then make a decision there (update apply to no or whatever), do wahtever prompt edits they want etc, then kick it back to the table in this tab. Though... they might want to *flag* for review as a batch activity and *then* go through *that list* as they see fit in the previous tab, or just ignore. Yes, they need a checkbox flag for review so that that's what load in the review tab, not all JDs from this session. I think it should still be to the left of the table tab because it is like going back. THen when this table is finalized it's finally resume time.
--->

**Session View — Tab 4: Tailoring**

- "Apply All" button (uses JD + resume, no extras)
- Individual cards: click → popup modal for adding app questions, additional JD text, selecting resume version, then "Go"
- Each Apply JD gets a status box: queued → processing → ready for review
- Click "ready" → opens output view: tailored resume, cover letter, app answers
- Editable before export/download as docx

<--- this actually needs to also go on the main table as a cell... they will not know if they need to interview prep until later, but I would like that button to very visible to customers potentially paying customers ;) so maybe it's good here to remind them that this tool can do that... but they will mostly likely either click it right after to test the output (let's give them 1 free interview prep markdown doc) or wait until later and click it from the full table after searching for their job they got the interview from. The bundle can give them a certain number of interview preps per month or bundle anyway and that will save our tokens for when they need them. I typically get separate prep docs for each interview even for the same company because they are different focuses so that is really helpful anyway. I keep it in the same chate (context) for me currently, so we'll use the cache and send back through when needed. But it's also a bit... idk how claude saves outside articles etc for re-reading - those are very important claude is able to read a lot of blogs and glassdoor and public releases etc so that context is important to save for later too --->
- "Continue for Interview Prep" button (appends structured context, opens new prompt)
let's let them know that they get 1 free on the button itself if they don't have a payed plan
--->

**Session View — Tab 4: Interviews**
for later, but holds my interview prep prompt and sends the cached convo back into a new claude chat. no batching here needed.

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

- Claude API (Sonnet for batch analysis, Sonnet for tailoring): ~$0.01–0.03 per JD analyzed, ~$0.05–0.15 per tailoring job <--- I'll have to test in the tool and in my manual method if I get good responses from both because I'm using claude opus 4.6 and the extended thinking is quite powerful for certain things. Can I even set the model in the API? Can i let the user do it and pay more for the higher model? I'd rather just use the highest model as long as the margins are acceptable. I'm not looking to make my fortune from this, just to have a real product and say I'm a real developer with a real LLC etc etc if I can... --->
- Per session (25 JDs, 6 Apply tailored): ~$0.50–1.50 in API costs
- Railway (Postgres + app): ~$5–10/month at low scale
- Pricing floor for paid sessions: $3–5 per session to maintain healthy margin

*(These are rough estimates — track actual costs from day one.)*<--- yeah now I'm gonna need to build observability scripts for the cost of course, and for the funnel conversions, but later I know I know --->
