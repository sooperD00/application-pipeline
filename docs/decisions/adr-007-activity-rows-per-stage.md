# ADR-007: Separate Activity Rows per Pipeline Stage

**Date**: 2026-02-28  
**Status**: Accepted

**Decision**: Each pipeline stage (application, phone_screen, interview_1..interview_7, offer, reject) is a separate `Activity` row linked to the same JD. *(Entity was initially called `TrackerEntry` during design — renamed in the models commit. See ADR-010 for the broader design change that motivated the rename.)*

**Rationale**: This models reality — each stage is a distinct event with its own date, prep, and outcome. It enables stage-level conversion analytics ("what's my phone screen to interview 1 pass rate?") without schema changes. Up to 7 interview slots covers even long chains.

**Alternatives considered**: Single row with stage as an updatable field (simpler but loses history — you can't see "applied 2/1, phone screen 2/8, interview 2/15" as a timeline). JSON array of stages in one row (queryable but ugly).
