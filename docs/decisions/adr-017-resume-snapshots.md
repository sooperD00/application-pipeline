# ADR-017: Resume Snapshots — Living Documents vs. Point-in-Time References (Phase 2+)

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

**Update 2026-09-17** — deferred from Phase 1+ to Phase 2+; the Phase 0 nullable-FK fix still stands and still carries the outputs. Tracked as [t-4baae5] in sprints/techdebt.md.
