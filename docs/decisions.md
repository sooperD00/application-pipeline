# Architecture Decision Records

Short entries documenting key technical decisions. Dated, with rationale and alternatives considered.

---

## ADR-001: Postgres over SQLite

**Date**: 2026-02-28  
**Status**: Accepted

**Decision**: Use Postgres (hosted on Railway) for all persistence.

**Rationale**: The application has concurrent background workers (parallel tailoring jobs writing results) while users browse the tracker. SQLite's write lock makes this a bottleneck. The data model is relational (sessions → JDs → tailoring jobs → activities) with cross-session queries for analytics. Railway offers one-click Postgres provisioning.

**Alternatives considered**: SQLite (simpler local dev, but write contention under concurrency). Could revisit for a fully local/offline mode later.

---

## ADR-002: React over Vue / Streamlit / FastHTML

**Date**: 2026-02-28  
**Status**: Accepted

**Decision**: React (via Vite) for the frontend.

**Rationale**: Three factors — (1) portfolio value: React appears in the majority of frontend-requiring JDs, having a real project in it is a career asset; (2) ecosystem: the card animation UI and SSE consumption have well-supported React libraries; (3) the UI has enough interactive complexity (fanned cards, drag-to-reorder, live status updates, tabbed views with background processing) that a framework designed for rich interactivity is warranted.

**Alternatives considered**: Vue (easier learning curve, smaller ecosystem), Streamlit (fast to prototype but fights you on custom layouts), FastHTML (Python-native but immature, limited component ecosystem).

---

## ADR-003: Claude Opus as Default Model

**Date**: 2026-02-28  
**Status**: Accepted

**Decision**: Use `claude-opus-4-6` for all API calls by default. Model is a config value, not hardcoded.

**Rationale**: The batch analysis phase benefits significantly from extended thinking and cross-JD reasoning. Resume tailoring quality directly impacts callback rates — this is the core value proposition and not the place to save pennies. Actual costs will be tracked from day one; pricing will be set after real data is in.

**Alternatives considered**: Sonnet for batch analysis (cheaper, possibly sufficient for simple fit/no-fit, but loses the strategic meta-analysis quality). Hybrid approach (Opus for analysis, Sonnet for tailoring) remains an option if costs are too high.

---

## ADR-004: TailoringJob Belongs to JD, Not Session

**Date**: 2026-02-28  
**Status**: Accepted

**Decision**: TailoringJob has a foreign key to JD, not to Session.

**Rationale**: Tailoring jobs outlive their session context. Interview prep happens days or weeks after the session. A user's interaction with a tailored application (reviewing, editing, continuing for interview prep) is JD-centric, not session-centric. Session-based ownership would require joining through Session → JD → TailoringJob for every interview prep query. Limit enforcement (free tier caps) can query by user through JD → Session → User.

**Alternatives considered**: Nesting under Session (simpler conceptual model but wrong ownership for the interview prep lifecycle).

---

## ADR-005: SSE for Analysis Progress, Polling for Tailoring

**Date**: 2026-02-28  
**Status**: Accepted

**Decision**: Batch analysis uses Server-Sent Events for real-time card updates. Tailoring jobs use polling.

**Rationale**: Analysis is a synchronous user experience — they're watching cards sort in real time, so sub-second updates matter. Tailoring is a "kick off and leave" experience — the user may navigate away, so polling on return (or when they visit Tab 4) is sufficient and simpler to implement.

**Alternatives considered**: WebSockets for everything (more complex, overkill for tailoring). Polling for everything (too slow for the card-sorting UX).

---

## ADR-006: Session = One Metadata Set

**Date**: 2026-02-28  
**Status**: Accepted

**Decision**: Each session is locked to one set of metadata (board, filters, search_term). New metadata = new session.

**Rationale**: This constraint enables clean funnel analytics. "Which search terms produce the most callbacks?" requires that each JD is tagged with exactly one search context. Mixed-metadata sessions would require per-JD metadata entry (25x more friction) or make the analytics unreliable.

**Alternatives considered**: Per-JD metadata (flexible but tedious). Metadata inheritance with per-JD override (complex, analytics become ambiguous).

---

## ADR-007: Separate Activity Rows per Pipeline Stage

**Date**: 2026-02-28  
**Status**: Accepted

**Decision**: Each pipeline stage (application, phone_screen, interview_1..interview_7, offer, reject) is a separate `Activity` row linked to the same JD. *(Entity was initially called `TrackerEntry` during design — renamed in the models commit. See ADR-010 for the broader design change that motivated the rename.)*

**Rationale**: This models reality — each stage is a distinct event with its own date, prep, and outcome. It enables stage-level conversion analytics ("what's my phone screen to interview 1 pass rate?") without schema changes. Up to 7 interview slots covers even long chains.

**Alternatives considered**: Single row with stage as an updatable field (simpler but loses history — you can't see "applied 2/1, phone screen 2/8, interview 2/15" as a timeline). JSON array of stages in one row (queryable but ugly).

---

## ADR-008: Parallel Tailoring via asyncio.Semaphore

**Date**: 2026-02-28  
**Status**: Accepted

**Decision**: Run up to 4 tailoring API calls concurrently using `asyncio.gather` with a semaphore. Free tier: 4. Paid tier: 8.

**Rationale**: Serial tailoring of 6 JDs could take 10+ minutes. Parallel cuts this to ~3 minutes. The semaphore pattern is simple, doesn't require external infrastructure (no Redis/Celery yet), and the concurrency limit is trivially adjustable per tier.

**Alternatives considered**: Serial (too slow, defeats the "leave and come back" UX). Unlimited parallel (risks API rate limits and cost spikes).

---

## ADR-009: File Storage in Postgres (Phase 0)

**Date**: 2026-02-28  
**Status**: Accepted (temporary)

**Decision**: Store generated docx files as `bytea` in Postgres. Resumes are text-only in Phase 0 — no binary storage needed for them yet.

**Rationale**: Phase 0 has 1-2 users with a handful of generated docs. External file storage adds deployment complexity for no benefit at this scale. Will migrate to S3-compatible storage when file volume or size warrants it.

**Alternatives considered**: S3 from the start (proper but premature). Local filesystem (doesn't survive Railway deploys).

---

## ADR-010: Activity Unifies Pipeline Stages and Action Items

**Date**: 2026-03-04  
**Status**: Accepted

**Decision**: Replace the original `TrackerEntry` design (pipeline stages only, with an `outcome` enum) with a single `Activity` table that holds both pipeline stages *and* action items (`follow_up`, `prep_doc`, `prep_time`, `thank_you`, `post_mortem`). Completion state is `completed_at IS NULL` — no separate outcome enum.

**Rationale**: The original `TrackerEntry` model treated the tracker as a read-only history log. In practice, each pipeline stage triggers a cluster of real to-dos: schedule prep, write thank-you, do a post-mortem. Keeping those in a separate table would require joining two places to answer "what do I need to do today?" The unified model means the active to-do list, time-to-hire analytics, and full stage history are all one query or one aggregate away from the same table.

`completed_at IS NULL` is simpler and more useful than an `outcome` enum. "Pending" was the only outcome that mattered for task management — pass/fail is captured implicitly by whether a subsequent stage was logged (phone screen followed by interview_1 = pass; phone screen followed by reject = fail). No outcome enum needed.

Action items are auto-generated by service-layer cascade templates when a user logs a pipeline stage — hardcoded offsets in Phase 0, configurable per-user in a later phase (same nullable-user_id pattern as `PromptTemplate`).

**Alternatives considered**: Separate `TrackerEntry` (stages) and `ActionItem` (to-dos) tables — cleaner conceptually but requires two queries for the active dashboard and a join for analytics. Single `TrackerEntry` with outcome enum retained — loses the to-do list capability and overfits to the history-log mental model.

---

## ADR-011: Dumb Renderer — Prompt Controls Formatting, Code Executes It

**Date**: 2026-03-05
**Status**: Accepted

**Decision**: The docx generation pipeline separates formatting *decisions* from formatting *execution*. Claude makes all formatting decisions (font sizes, bold/italic ranges, spacing, element ordering) guided by the `resume_generation` prompt template. Claude returns structured JSON describing the document element-by-element. `docx_builder.py` is a "dumb renderer" — it walks the JSON array and translates each element into python-docx calls without making any formatting choices of its own.

**Rationale**: The current manual workflow already works this way: a prompt tells Claude what formatting rules to follow, and Claude produces a docx with nuanced, per-JD formatting decisions (orphan bullet management, bold emphasis storytelling, whitespace calibrated to audience). Hardcoding formatting rules into Python would:

1. **Lose per-JD adaptability.** Claude currently adjusts formatting based on content length, audience, and emphasis needs. A rigid template can't do this.
2. **Lock formatting behind code changes.** Users (including future users with different preferences) would need a developer to change their resume style. With prompt-driven formatting, they edit a text template in the UI.
3. **Block the Phase N resume uploader.** The planned workflow is: user uploads a docx → system parses formatting into a prompt template → Claude uses that template for future tailoring. This requires formatting to live in prompt-space, not code-space.

The JSON schema is the contract between Claude and the renderer. It's expressive enough for Claude to communicate fine-grained decisions (per-element font sizes, specific bold substrings, hyperlink placement) while being simple enough for the renderer to stay truly dumb.

**The test**: If a user changes their prompt to say "use 12pt for everything and never bold anything," the system should honor it without a code change. With this architecture, it does.

**What the renderer hardcodes** (document-level, not content-level): page size (US Letter), margins, default font family (Calibri). These become configurable in a future sprint via a document-settings template.

**Alternatives considered**: 
- python-docx template with formatting hardcoded in Python (fast to build, but violates all three points above — formatting decisions would be split between prompt and code with no clear ownership).
- Claude returns raw docx bytes directly (not feasible — the API returns text, not binary files).
- Claude returns markdown, Python converts to docx (loses fine-grained formatting control; markdown can't express per-element font sizes or bold substrings).

---

## ADR-012: Split cover_letter and app_answers Into Separate Templates

**Date**: 2026-03-05
**Status**: Accepted

**Decision**: The `cover_letter_app_answers` PromptPhase is split into two separate phases: `cover_letter` and `app_answers`. Each gets its own PromptTemplate row, its own editable text box in the UI, and independent toggle conditions.

**Rationale**: Cover letters and application answers have different activation conditions already modeled in the data: `jd.cover_letter_requested` gates cover letters, `jd.app_questions` being populated gates app answers. Combining them in one template forces awkward partial-inclusion logic and prevents users from reading and editing them independently. The separation also means Claude's response JSON has separate fields for each, making parsing unambiguous.

**Migration note**: The Postgres enum retains the old `cover_letter_app_answers` value (can't DROP VALUE from a Postgres enum) but it is no longer referenced in application code.

**Alternatives considered**: Keep combined (simpler schema, but wrong separation of concerns for both the UI and the conditional logic).

---

## ADR-013: Two-Layer Prompt Architecture — Public Templates vs. Private System Prompts

**Date**: 2026-03-07
**Status**: Proposed (deferred past MVP)

**Decision**: The prompt system has two layers that serve different purposes and have different visibility rules:

1. **PromptTemplate rows** (DB, `prompt_templates` table) — user-facing. These are the editable templates the UI exposes: analysis, resume_generation, cover_letter, app_answers. Users can read, fork, and version them. System defaults ship via the seed script. This is the product surface.

2. **`prompts/` directory** (files on disk, gitignored or kept private) — operator-facing. These are the *real* system prompts and meta-instructions: how the platform talks to Claude under the hood, what structured JSON schema to return, how to reason about fit assessment, what tone to use. The stuff that makes the output quality good. Users never see these; they're loaded at startup or embedded in the service layer.

The distinction matters because the repo is public. The PromptTemplate content is the "what" — users customize it and that's the product. The system prompts are the "how" — the prompt engineering that makes Claude's output worth paying for. Publishing the system prompts in a public repo hands competitors the most valuable part of the codebase for free.

**Current state**: System prompts are hardcoded as string constants in `services/analysis.py` and `services/tailoring.py`. This works but means they're visible in the public repo today. The `prompts/` directory in the README tree is a placeholder for extracting them to files that can be gitignored or loaded from a private source.

**When to implement**: Before the LinkedIn blog post / public launch. Not needed for MVP (Nicole is the only user and the repo has no traffic yet).

**Alternatives considered**: 
- Keep everything in the DB (simpler, but then system prompts are editable by users, which defeats the purpose — or you need a visibility flag and access control).
- Environment variables for system prompts (awkward for multi-paragraph text).
- Private git submodule (clean separation, but adds deployment complexity).
- Accept the risk (the workflow design and UX are the real moat, not the prompts). Possibly true, but no reason to give it away before testing that hypothesis.

---

## ADR-014: Application Package — Zip Download per Tailoring Job

**Date**: 2026-03-07
**Status**: Accepted (shipped Sprint 11)

**Decision**: Add a zip download endpoint that bundles all outputs for a single tailoring job into one file. The user gets a ready-to-use folder they can open in their file manager and work from.

**Contents of the zip**:

```
CompanyName_RoleName/
  resume.docx                  ← output_resume_docx (the tailored resume)
  jd.txt                       ← cleaned_text + metadata (company, role, link, compensation)
  cover_letter.txt             ← output_cover_letter (omitted if not requested)
  app_questions.txt            ← output_app_answers (omitted if no questions)
  analysis.txt                 ← analysis_text + requirements_met (Claude's fit assessment)
  notes.txt                    ← placeholder for the human to add notes after download
```

**Rationale**: The current workflow after tailoring is: download the docx, then mentally reconstruct which JD it was for, then go find the cover letter text in the app, then copy-paste app answers somewhere. That's 4 trips to the app for one application submission. The zip bundles everything the human needs to sit down and apply — open the folder, review the resume in Word, paste the cover letter, paste app answers, and move on.

`notes.txt` ships empty with a header line (company, role, date). It's where the human jots "submitted 3/8, heard back 3/12, phone screen scheduled 3/15" — a portable paper trail that lives with the application files even if the app is offline. This becomes more useful when Activity tracking is built (Phase 1), but the file is free to include now.

The txt files are plain text, not markdown or docx, because the user is pasting them into web forms on application sites. No formatting to strip.

**Endpoint**: `GET /api/jds/{id}/tailoring/{job_id}/package` — returns a zip. Sits next to the existing `/docx` endpoint. Backend assembles the zip in memory using Python's `zipfile` module (no temp files, no disk writes). The zip is small (~50-100KB for text + one docx).

**What this needs**: One new endpoint in `jds.py`, ~40 lines. No new models, no migrations, no new services. All data is already in TailoringJob + JD rows. Shipped in Sprint 11.

**Alternatives considered**:
- Frontend-assembled zip (JSZip library, multiple fetch calls): works but slower, adds a JS dependency, and the frontend has to know the file layout. Backend already has all the data in one query.
- Individual download buttons per file: forces the user to click 4-5 times and organize the files themselves. Defeats the purpose.
- Include raw_text alongside cleaned_text: adds noise. The cleaned version is what Claude analyzed. Raw is available in-app via "view raw" toggle if needed.

---

## ADR-015: Session-Scoped Nav Tabs Visible at All Times (Grayed When Inactive)

**Date**: 2026-03-09  
**Status**: Accepted

**Decision**: The top nav always shows all five workflow tabs — Scrape & Analyze, Calibrate, Review & Enrich, Tailoring, Resumes — regardless of whether a session is selected. Session-scoped tabs (Calibrate, Review & Enrich, Tailoring) render grayed out / disabled when no session is active. Clicking a disabled tab shows a tooltip: "Select or create a session to unlock this step."

**Rationale**: The tab bar *is* the product story. A first-time visitor (or a hiring manager watching a demo) should see the full workflow — paste, analyze, calibrate, review, tailor — without having to start a session to discover what happens after step one. Five tabs is well within comfortable horizontal nav density; clutter becomes a real concern around 8+. The 2:3 active-to-disabled ratio when no session is selected reads as "there's more to unlock," not "this app is broken." This is the checklist principle: the user reads the whole pipeline before starting it, which sets expectations for the session-as-a-unit-of-work model (ADR-006).

**Alternatives considered**: Show session-scoped tabs only after entering a session (cleaner layout, but hides the product's feature surface from new users and breaks the mental model of "session = these five steps"). Dynamic nav was the more conventional UX choice, but this app doubles as a portfolio piece and a potential product — discoverability wins over minimalism here.

---

## ADR-016: Entity Lifecycle and Route Hierarchy (Phase ?)

**Date**: 2026-03-11  
**Status**: Accepted

**Decision:** JDs graduate from session-scoped to independent entities; /sessions is the funnel, /tracking becomes index, /pursuits/:jd_id owns post-callback workflows. Context: the manual workflow folder structure, the 500→100→5 funnel, and the fact that session context is captured as data on the JD, not a route dependency.

---

## ADR-017: Resume Snapshots — Living Documents vs. Point-in-Time References (Phase 1+)

**Date**: 2026-03-12  
**Status**: Proposed (Phase 0 ships the nullable FK fix; snapshot architecture deferred)

**Context:** Resumes are living documents — users edit, delete, and replace them between sessions. But analyses and tailoring jobs need to reference the resume content *as it existed when the job ran*. Phase 0 papers over this: `prompt_snapshot` on TailoringJob freezes the full prompt (including resume text) at kick-off, and analysis results are self-contained in `analysis_text`. Outputs are safe. But the FK from TailoringJob → Resume is fragile — deleting a resume broke the constraint (Sprint 9 fix: `ondelete=SET NULL`), and there's no way to ask "which resume versions did this session's analysis use?"

**Decision:** Phase 1 introduces a `session_resume_snapshots` table: `(id, session_id, source_resume_id, label, content, snapshotted_at)`. When analysis runs, the system copies current resume content into snapshots scoped to that session. Analysis and tailoring reference snapshots, not the live Resumes table. The Resumes tab remains the "workshop" for editing current versions; sessions consume frozen copies.

The tailoring page offers a choice: use cached snapshots from the session analysis, or pull current resume versions (creating new snapshots). This matters because Claude does a similar fit analysis on the single JD during tailoring — the user may want to use an updated resume if they've revised it since the session analysis.

Session locking follows naturally: once analysis runs, the session's resume snapshots are immutable. A "Clone Session" button lets users re-run the same JD set with updated resumes.

**Phase 0 fix (Sprint 9):** `resume_id` on TailoringJob becomes nullable with `ondelete=SET NULL`. Response models in jds.py and sessions.py updated to `UUID | None`. Outputs (prompt_snapshot, output_resume, output_resume_docx) remain intact after resume deletion. This is the minimum viable fix — it unblocks resume deletion without the full snapshot architecture.

**Alternatives considered:**

1. **Copy-on-write resumes** (new row on every edit, version column): simpler than a separate snapshot table, but pollutes the Resumes table with historical versions the user doesn't want to see in their "workshop" view. Adds complexity to the 3-resume cap (count active versions only? all versions?).

2. **Soft-delete resumes** (is_deleted flag): solves the FK problem but doesn't solve the "which version was used" problem. A deleted resume preserves the row but not the edit history.

3. **Embed resume text directly in TailoringJob** (no FK at all): already partially done via prompt_snapshot, but loses the ability to show "this job used your 'Technical' resume" in the UI. The snapshot table preserves both the content and the label/metadata link.