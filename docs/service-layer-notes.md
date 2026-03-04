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

Three PromptTemplate rows composed into one Claude API call:

1. **analysis** — always included
2. **resume_generation** — always included (contains docx formatting instructions)
3. **cover_letter_app_answers** — included only if `jd.cover_letter_requested` or `jd.app_questions` is populated

- [ ] `assemble_tailoring_prompt(jd, resume, user)` — fetches active templates for each phase, concatenates in order, substitutes variables ({jd_text}, {resume}, {company}, etc.)
- [ ] `prompt_snapshot` on TailoringJob stores the assembled result, frozen at kick-off

---

## Docx Generation (data flow reminder)

The prompt tells Claude to produce a docx directly — formatting instructions live in the `resume_generation` prompt, not in a python-docx template layer.

```
prompt (with formatting instructions) → Claude → docx bytes → output_resume_docx
                                                      ↓
                                               extract text → output_resume (for display/comparison)
```

- [ ] `output_resume` is derived FROM the docx, not an input TO it
- [ ] Phase N: resume uploader tab analyzes user's existing docx for style preferences, feeds into prompt

---

## Analytics (derived from Activity, no extra tables needed)

All computable at query time from the activities table:

- **Time-to-hire per JD**: `MAX(completed_at) - MIN(completed_at)` where jd_id matches
- **Weekly application count**: `GROUP BY date_trunc('week', completed_at)` where activity_type = 'application'
- **Stage conversion rates**: count of completed activities at stage N vs stage N+1 per JD
- **Follow-up compliance**: activities where type = 'follow_up' and completed_at <= due_date vs overdue
- **Search term effectiveness**: join through JD → Session to get search_term, correlate with pipeline depth reached
