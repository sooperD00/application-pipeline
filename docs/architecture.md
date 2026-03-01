# Architecture

## Data Model

Six core entities, each a SQLModel table. Foreign keys are explicit. No deep nesting — TailoringJob belongs to JD, not Session.

```
┌──────────┐     ┌──────────────┐     ┌──────────────────┐
│   User   │────<│   Session    │────<│       JD         │
└──────────┘     └──────────────┘     └──────────────────┘
     │                                    │           │
     │                                    │           │
     ├───<┌──────────┐                    ├───<┌──────────────┐
     │    │  Resume   │                    │   │TailoringJob  │
     │    └──────────┘                    │   └──────────────┘
     │                                    │
     ├───<┌────────────────┐              ├───<┌──────────────┐
          │PromptTemplate  │                   │TrackerEntry  │
          └────────────────┘                   └──────────────┘
```

### User

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | PK |
| email | str, nullable | null for anonymous sessions |
| session_token | str | cookie-based, always present |
| created_at | datetime | |
| token_expires_at | datetime | 7 days for anonymous, null for accounts |

### Resume

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | PK |
| user_id | UUID | FK → User |
| label | str | user-assigned, e.g. "Technical", "Leadership" |
| filename | str | original upload filename |
| file_data | bytes | stored file |
| extracted_text | text | for sending to Claude |
| created_at | datetime | |

Constraint: max 3 per user (enforced at API layer).

### PromptTemplate

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | PK |
| user_id | UUID, nullable | FK → User. null = system default |
| phase | enum | analysis, calibrate, tailoring, compare, interview_prep |
| name | str | user-facing label |
| template_text | text | with variable slots: {jd_text}, {resume}, {metadata}, etc. |
| version | int | auto-increment per user+phase |
| is_active | bool | which version is currently in use |
| created_at | datetime | |

### Session

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | PK |
| user_id | UUID | FK → User |
| board | str | LinkedIn, Indeed, etc. |
| filters | str | "remote, last 24 hours" — free text |
| search_term | str | the keyword used |
| meta_analysis | text, nullable | Claude's rolling cross-JD summary |
| status | enum | active, analyzing, complete |
| created_at | datetime | |

### JD

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | PK |
| session_id | UUID | FK → Session |
| number | int | position in session (1-25), maps to job board order |
| raw_text | text | as pasted |
| cleaned_text | text | auto-cleaned |
| company | str | extracted or user-entered |
| role | str | extracted or user-entered |
| compensation | str, nullable | salary range, equity, etc. — free text |
| employee_count | str, nullable | |
| link | str, nullable | application URL |
| status | enum | pending, apply, maybe, no |
| status_source | enum | ai, user | who set the current status |
| analysis_text | text, nullable | Claude's full analysis |
| requirements_met | JSON, nullable | structured: [{requirement, status, notes}] |
| app_questions | text, nullable | pasted from application site |
| additional_jd_text | text, nullable | from application website if different |
| cover_letter_requested | bool | default false |
| flagged_for_review | bool | default false, sends to Calibrate tab |
| created_at | datetime | |

### TailoringJob

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | PK |
| jd_id | UUID | FK → JD |
| resume_id | UUID | FK → Resume |
| prompt_snapshot | text | exact prompt used (frozen at kick-off) |
| status | enum | queued, processing, ready, reviewed |
| output_resume | text, nullable | tailored resume content |
| output_cover_letter | text, nullable | |
| output_app_answers | JSON, nullable | [{question, answer}] |
| output_resume_docx | bytes, nullable | generated file |
| chat_context | JSON, nullable | structured context for continuation |
| model_used | str | "claude-opus-4-6" etc. |
| api_cost_cents | int, nullable | tracked per job |
| created_at | datetime | |
| completed_at | datetime, nullable | |

### TrackerEntry

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | PK |
| jd_id | UUID | FK → JD |
| stage | enum | application, phone_screen, interview_1..interview_7, offer, reject |
| date | date | when this stage occurred |
| outcome | enum | pending, pass, fail |
| notes | text, nullable | |
| week_number | int | ISO week, derived from date |
| created_at | datetime | |

## API Contracts

### Sessions & JDs

```
POST   /api/sessions                    → create session (metadata)
GET    /api/sessions/{id}               → full session state (with JDs)
POST   /api/sessions/{id}/jds           → add JD (auto-cleans)
POST   /api/sessions/{id}/analyze       → kick off batch analysis (SSE)
POST   /api/sessions/{id}/batch-tailor  → apply-all (up to 4 parallel)

GET    /api/jds/{id}                    → single JD with all relations
PATCH  /api/jds/{id}                    → update status, app_questions, etc.
POST   /api/jds/{id}/tailoring          → kick off single tailoring job
GET    /api/jds/{id}/tailoring/{job_id} → tailoring status + outputs
```

### Resumes

```
POST   /api/resumes          → upload (multipart, with label)
GET    /api/resumes           → list user's resumes
DELETE /api/resumes/{id}      → delete
```

### Tracker

```
GET    /api/tracker                     → all entries (filterable)
GET    /api/tracker/weekly              → grouped by week with counts
POST   /api/tracker                     → add entry (usually auto-created on tailoring complete)
PATCH  /api/tracker/{id}               → update stage, outcome, notes
```

### Analysis SSE Stream

`POST /api/sessions/{id}/analyze` returns a Server-Sent Events stream:

```
event: batch_start
data: {"batch": 1, "jd_numbers": [1,2,3,4,5]}

event: jd_result
data: {"jd_id": "...", "number": 1, "status": "apply", "analysis": "...", "requirements": [...]}

event: jd_result
data: {"jd_id": "...", "number": 2, "status": "no", "analysis": "...", "requirements": [...]}

...

event: batch_complete
data: {"batch": 1, "meta_analysis": "Updated summary text..."}

event: batch_start
data: {"batch": 2, "jd_numbers": [6,7,8,9,10]}

...

event: analysis_complete
data: {"session_id": "...", "summary": {"apply": 6, "maybe": 3, "no": 16}}
```

## Claude API Integration

### Conversation Management

The platform manages conversations, not raw API calls. Each conversation type has its own lifecycle:

**Batch Analysis**: One conversation per session. JDs appended in batches of 5. The system prompt includes instructions for structured output (status, analysis, requirements breakdown) and meta-analysis. The conversation is stored for context but not user-visible.

**Tailoring**: One conversation per Apply JD. Context assembled from: JD + metadata + selected resume + analysis from batch + app questions (if any). Output is parsed into structured fields. Conversation is persisted for continuation (interview prep). Up to 4 run in parallel via `asyncio.gather`.

**Calibrate**: One conversation per user interaction. Loads flagged JD(s) or meta-analysis + resume. User-editable prompt. Free-form — output displayed as-is in a chat-like interface.

### Model Configuration

Default: `claude-opus-4-6`. Stored as a config value, changeable without code deployment. Future: user-selectable with price differential.

### Context Continuation

When a user clicks "Continue for Interview Prep" on a completed tailoring job, the platform assembles a new conversation with:
- The original JD
- The tailored resume that was generated  
- The analysis from batch phase
- Application questions and answers if they exist
- Any tracker notes (interview dates, stages completed)

This is structured context assembly, not a raw chat history replay.

## Background Processing

### Phase 0: FastAPI BackgroundTasks

Simple and sufficient for 1-2 users. Tailoring jobs are kicked off as background tasks. Status is polled by the frontend.

### Phase 1+: arq + Redis

When concurrent users make BackgroundTasks unreliable (tasks die with the request), move to arq for proper job queuing with:
- Retry logic
- Job status persistence
- Concurrency limits
- Dead letter handling

### Parallel Execution

Tailoring jobs run up to 4 in parallel:

```python
async def batch_tailor(jd_ids: list[UUID]):
    semaphore = asyncio.Semaphore(4)
    
    async def tailor_one(jd_id):
        async with semaphore:
            # call Claude API, store results
            ...
    
    await asyncio.gather(*[tailor_one(jd_id) for jd_id in jd_ids])
```

Free tier: 4 parallel. Paid tier: 8 parallel (just change the semaphore).

## Text Cleaning Pipeline

Applied on JD ingest (`POST /sessions/{id}/jds`):

1. Strip leading/trailing whitespace
2. Normalize line endings (CRLF → LF)
3. Collapse 3+ consecutive newlines to 2
4. Remove non-printable characters (except newlines and tabs)
5. Normalize unicode whitespace to ASCII
6. Strip zero-width characters

Raw text stored separately for "view raw" toggle.

## File Storage

Phase 0: Postgres `bytea` columns for resume uploads and generated docx files. Simple, no external dependencies.

Phase 1+: If file sizes or volume become an issue, move to S3-compatible storage (Railway supports this) with URLs in the database.
