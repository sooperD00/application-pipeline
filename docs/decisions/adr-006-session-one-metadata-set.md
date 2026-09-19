# ADR-006: Session = One Metadata Set

**Date**: 2026-02-28  
**Status**: Accepted

**Decision**: Each session is locked to one set of metadata (board, filters, search_term). New metadata = new session.

**Rationale**: This constraint enables clean funnel analytics. "Which search terms produce the most callbacks?" requires that each JD is tagged with exactly one search context. Mixed-metadata sessions would require per-JD metadata entry (25x more friction) or make the analytics unreliable.

**Alternatives considered**: Per-JD metadata (flexible but tedious). Metadata inheritance with per-JD override (complex, analytics become ambiguous).
