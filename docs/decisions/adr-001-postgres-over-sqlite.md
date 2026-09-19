# ADR-001: Postgres over SQLite

**Date**: 2026-02-28  
**Status**: Accepted

**Decision**: Use Postgres (hosted on Railway) for all persistence.

**Rationale**: The application has concurrent background workers (parallel tailoring jobs writing results) while users browse the tracker. SQLite's write lock makes this a bottleneck. The data model is relational (sessions → JDs → tailoring jobs → activities) with cross-session queries for analytics. Railway offers one-click Postgres provisioning.

**Alternatives considered**: SQLite (simpler local dev, but write contention under concurrency). Could revisit for a fully local/offline mode later.
