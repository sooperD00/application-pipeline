# Architecture Decision Records

Short entries documenting key technical decisions. Dated, with rationale and alternatives
considered. One record per file, `adr-<NNN>-<short-name>.md`. Numbers are identity: they are
assigned once, never reused, and never renumbered, so anything may cite a record by its ID.

Start a new record by copying [adr-000-adr-template.md](adr-000-adr-template.md), which carries
the house format and the rules for numbering one.

ADR-019 and ADR-020 are reserved — Google sign-in writes 019, and the credit-ledger pricing
rule writes 020.

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| 001 | [Postgres over SQLite](adr-001-postgres-over-sqlite.md) | Accepted | 2026-02-28 |
| 002 | [React over Vue / Streamlit / FastHTML](adr-002-react-frontend.md) | Accepted | 2026-02-28 |
| 003 | [Claude Opus as Default Model](adr-003-claude-opus-default-model.md) | Accepted | 2026-02-28 |
| 004 | [TailoringJob Belongs to JD, Not Session](adr-004-tailoringjob-belongs-to-jd.md) | Accepted | 2026-02-28 |
| 005 | [SSE for Analysis Progress, Polling for Tailoring](adr-005-sse-and-polling.md) | Accepted | 2026-02-28 |
| 006 | [Session = One Metadata Set](adr-006-session-one-metadata-set.md) | Accepted | 2026-02-28 |
| 007 | [Separate Activity Rows per Pipeline Stage](adr-007-activity-rows-per-stage.md) | Accepted | 2026-02-28 |
| 008 | [Parallel Tailoring via asyncio.Semaphore](adr-008-parallel-tailoring-semaphore.md) | Accepted | 2026-02-28 |
| 009 | [File Storage in Postgres (Phase 0)](adr-009-file-storage-in-postgres.md) | Accepted | 2026-02-28 |
| 010 | [Activity Unifies Pipeline Stages and Action Items](adr-010-activity-unifies-stages.md) | Accepted | 2026-03-04 |
| 011 | [Dumb Renderer — Prompt Controls Formatting, Code Executes It](adr-011-dumb-renderer.md) | Accepted | 2026-03-05 |
| 012 | [Split cover_letter and app_answers Into Separate Templates](adr-012-split-cover-letter-and-app-answers.md) | Accepted | 2026-03-05 |
| 013 | [Two-Layer Prompt Architecture — Public Templates vs. Private System Prompts](adr-013-two-layer-prompt-architecture.md) | Proposed | 2026-03-07 |
| 014 | [Application Package — Zip Download per Tailoring Job](adr-014-application-package-zip.md) | Accepted | 2026-03-07 |
| 015 | [Session-Scoped Nav Tabs Visible at All Times (Grayed When Inactive)](adr-015-session-scoped-nav-tabs.md) | Accepted | 2026-03-09 |
| 016 | [Entity Lifecycle and Route Hierarchy (Phase ?)](adr-016-entity-lifecycle-and-routes.md) | Accepted | 2026-03-11 |
| 017 | [Resume Snapshots — Living Documents vs. Point-in-Time References (Phase 2+)](adr-017-resume-snapshots.md) | Proposed | 2026-03-12 |
| 018 | [uv for Backend Dependency Management](adr-018-uv-for-backend-dependencies.md) | Accepted | 2026-08-30 |
| 021 | [Planning System — Sprint Files, Stable IDs, and In-Source Cleanup Markers](adr-021-planning-system.md) | Proposed | 2026-09-19 |
