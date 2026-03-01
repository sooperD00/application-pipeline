# Architecture Decision Records

Short entries documenting key technical decisions. Dated, with rationale and alternatives considered.

---

## ADR-001: Postgres over SQLite

**Date**: 2026-02-28  
**Status**: Accepted

**Decision**: Use Postgres (hosted on Railway) for all persistence.

**Rationale**: The application has concurrent background workers (parallel tailoring jobs writing results) while users browse the tracker. SQLite's write lock makes this a bottleneck. The data model is relational (sessions → JDs → tailoring jobs → tracker entries) with cross-session queries for analytics. Railway offers one-click Postgres provisioning.

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

## ADR-007: Separate Tracker Rows per Interview Stage

**Date**: 2026-02-28  
**Status**: Accepted

**Decision**: Each interview stage (application, phone screen, interview 1-7, offer, reject) is a separate TrackerEntry row linked to the same JD.

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

**Decision**: Store resume uploads and generated docx files as `bytea` in Postgres.

**Rationale**: Phase 0 has 1-2 users with at most 3 resumes and a handful of generated docs. External file storage adds deployment complexity for no benefit at this scale. Will migrate to S3-compatible storage when file volume or size warrants it.

**Alternatives considered**: S3 from the start (proper but premature). Local filesystem (doesn't survive Railway deploys).
