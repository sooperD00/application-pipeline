# ADR-009: File Storage in Postgres (Phase 0)

**Date**: 2026-02-28  
**Status**: Accepted (temporary)

**Decision**: Store generated docx files as `bytea` in Postgres. Resumes are text-only in Phase 0 — no binary storage needed for them yet.

**Rationale**: Phase 0 has 1-2 users with a handful of generated docs. External file storage adds deployment complexity for no benefit at this scale. Will migrate to S3-compatible storage when file volume or size warrants it.

**Alternatives considered**: S3 from the start (proper but premature). Local filesystem (doesn't survive Railway deploys).
