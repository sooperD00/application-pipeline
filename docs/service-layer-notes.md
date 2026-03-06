# Service Layer Implementation Notes

Decisions made during models.py review that need implementation outside the data model.

---

## API-Layer Limits (pattern: count-check-before-insert)

All limits enforced at the API layer, not the DB. Same 3-line pattern everywhere. Put values in a config YAML when you implement.

- [ ] **Resume**: max 3 per user
- [ ] **PromptTemplate**: max N versions per user+phase+name (pick N when you see usage; 10 is fine for now)
- [ ] **Session**: uncapped for Phase 0 (free tier caps in Phase 3)
- [ ] **JD**: max 25 per session
- [ ] **TailoringJob**: no row limit, but semaphore caps concurrent execution (4 free, 8 paid)

---

## Activity Cascade (service layer, not DB)

When a user logs a pipeline stage with a date, auto-generate child activities with offset due dates.

```python
# Hardcoded Phase 0. Becomes a workflow_templates table in Phase N.
ACTIVITY_TEMPLATES = {
    "phone_screen_scheduled": [
        {"type": "prep_doc",    "due_offset_days": -1},
        {"type": "prep_time",   "due_offset_days": -1},
        {"type": "thank_you",   "due_offset_days":  1},
        {"type": "post_mortem", "due_offset_days":  0},
    ],
    "interview_scheduled": [
        {"type": "prep_doc",    "due_offset_days": -3},
        {"type": "prep_time",   "due_offset_days": -1},
        {"type": "thank_you",   "due_offset_days":  1},
        {"type": "post_mortem", "due_offset_days":  0},
    ],
    "application_submitted": [
        {"type": "follow_up",   "due_offset_days":  7},
    ],
}
```

Implementation: plain sync function in `services.py`, called from the FastAPI route. No async, no background task — it's 5 rows on a button click.

- [ ] `schedule_activities(jd_id, trigger, anchor_date, session)` — looks up template, bulk-inserts Activity rows
- [ ] Follow-up days per stage should be user-configurable eventually (same nullable-user_id pattern as PromptTemplate, but a simple settings table — Phase N)

---

## Active Applications View (frontend query)

The "Active Applications" tab is a filtered query, not a separate data structure:

```sql
SELECT DISTINCT jd_id FROM activities
WHERE completed_at IS NULL           -- has open to-dos
   OR activity_type IN ('application', 'phone_screen', 'interview_1', ...)
                                     -- is in the pipeline
AND activity_type NOT IN ('reject')  -- not dead
ORDER BY due_date ASC NULLS LAST     -- urgent stuff first
```

- [ ] API endpoint: `GET /api/activities/active` — returns JDs with their open activities, sorted by nearest due date
- [ ] Frontend: star/badge on JD rows with pending activities, alert indicator on the tab itself
- [ ] "Waiting on reply" = an activity with `due_date = NULL` and `completed_at = NULL` — sorts to the bottom

---

## Prompt Assembly for Tailoring (service layer)

Four PromptTemplate rows composed into one Claude API call:

1. **analysis** — always included
2. **resume_generation** — always included (contains docx formatting instructions, ADR-011)
3. **cover_letter** — included only if `jd.cover_letter_requested` (ADR-012)
4. **app_answers** — included only if `jd.app_questions` is populated (ADR-012)

- [ ] `assemble_tailoring_prompt(jd, resume, user)` — fetches active templates for each phase, concatenates in order, substitutes variables ({jd_text}, {resume}, {company}, etc.)
- [ ] `prompt_snapshot` on TailoringJob stores the assembled result, frozen at kick-off

---

## Docx Generation (data flow reminder — ADR-011)

The prompt tells Claude what formatting to use. Claude returns structured JSON describing each element (font sizes, bold ranges, spacing). `docx_builder.py` is a dumb renderer — it walks the JSON and makes python-docx calls without formatting decisions of its own.

```
prompt (with formatting instructions) → Claude → structured JSON → docx_builder.py → docx bytes → output_resume_docx
                                                                                          ↓
                                                                                   extract text → output_resume (for display/comparison)
```

- [ ] `output_resume` is derived FROM the docx, not an input TO it
- [ ] Phase N: resume uploader tab analyzes user's existing docx for style preferences, feeds into prompt

---

## Ownership Chain on TailoringJob

TailoringJob → JD → Session → User is 3 hops. Fine for Phase 0 (always entering through a specific JD). If Phase 1+ adds a listing endpoint like GET /api/tailoring-jobs (all my jobs), consider denormalizing user_id onto TailoringJob or adding a composite index.

---

## Analytics (derived from Activity, no extra tables needed)

All computable at query time from the activities table:

- **Time-to-hire per JD**: `MAX(completed_at) - MIN(completed_at)` where jd_id matches
- **Weekly application count**: `GROUP BY date_trunc('week', completed_at)` where activity_type = 'application'
- **Stage conversion rates**: count of completed activities at stage N vs stage N+1 per JD
- **Follow-up compliance**: activities where type = 'follow_up' and completed_at <= due_date vs overdue
- **Search term effectiveness**: join through JD → Session to get search_term, correlate with pipeline depth reached

---

## Free Tier Tailoring Cap (Phase 3)

Cap total tailoring jobs per free session, not just parallelism. Semaphore (ADR-008) controls concurrent execution. A separate count-check (same pattern as resume cap and JD cap) controls total jobs per session.

Proposed: 6 tailoring jobs per session (free), uncapped (paid). Parallelism stays at 4/8.

Cost context: each Opus tailoring call is ~$0.30–0.60. Uncapped free tier at 25 JDs = up to $15/session with zero revenue. The cap is both a business gate and a cost control.

Phase 1 concern: semaphore is per-session. Multi-user needs a global rate limiter (per API key) to stay within Anthropic's RPM limits.

---

## Missing Endpoint: GET /api/sessions (list all) - DO IN SPRINT 6

No way to list sessions without knowing the ID. The seed script prints it, but a frontend session picker needs GET /api/sessions → all sessions for current user, ordered by created_at desc. Low effort, add when the frontend
needs it.

---

## Tailoring Analysis/Strategy Not Surfaced - DO IN SPRINT 6

Claude returns "analysis" and "strategy" fields in the tailoring response. Currently only saved inside chat_context (full conversation JSON). Add dedicated columns or parse them out for display when the frontend needs 
a "why did Claude make these choices" view per tailoring job. Quick fix when you want it: two lines in run_tailoring_job to pull parsed.get("analysis") and parsed.get("strategy") into new columns or into the existing analysis_text field on the JD.

---

## Batch-Tailor: Skip Already-Tailored JDs? - DO IN SPRINT 6

Currently batch-tailor creates jobs for ALL apply-status JDs, even if they already have a completed tailoring job. This is correct for re-tailoring after prompt/resume changes, but means accidental double-clicks double the API cost. Consider: skip JDs with status=ready unless a force flag is passed. Or surface "already tailored" in the UI and let the user decide.

---

## Batch-Tailor Response Should Pair job_id + jd_id - DONE 3/5/26 Sprint 5 fix

Current response: {"job_ids": [...], "jd_count": N}
Should be: {"jobs": [{"job_id": "...", "jd_id": "..."}, ...], "jd_count": N}

The docx download endpoint requires both jd_id and job_id. Without pairing them in the batch response, the frontend has to poll each job_id individually just to learn which JD it belongs to. Fix in sessions.py BatchTailorResponse schema and the endpoint return value.

---

## Batch Tailoring Status Endpoints (needed for frontend) - DO IN SPRINT 6

GET /api/sessions/{id}/tailoring-jobs
  All tailoring jobs across all JDs in a session. The frontend needs this after batch-tailor to show a dashboard of progress without N individual polling calls. Return: [{job_id, jd_id, status, company, role, has_docx}]

GET /api/jds/{id}/tailoring
  All tailoring jobs for a single JD. Useful for the JD detail view to show re-tailor history. Return: [{job_id, status, created_at, has_docx}]

Neither exists yet. The frontend currently has to poll each job individually via GET /jds/{jd_id}/tailoring/{job_id}. Works but scales badly — a session with 6 apply JDs means 6 polling loops.


---

## Router Organization: Tailoring Endpoints

Sprint 5 put tailoring endpoints in the routers that own their URL prefixes:
  - POST/GET /api/jds/{id}/tailoring/...  → jds.py
  - POST /api/sessions/{id}/batch-tailor  → sessions.py

The original plan had a separate routers/tailoring.py. Consider splitting 
if jds.py gets too long or if tailoring grows its own concepts (re-tailor, 
compare, prompt preview) that don't feel like JD operations anymore.
services/tailoring.py stays either way — only the router layer would move.