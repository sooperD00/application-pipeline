# ADR-005: SSE for Analysis Progress, Polling for Tailoring

**Date**: 2026-02-28  
**Status**: Accepted

**Decision**: Batch analysis uses Server-Sent Events for real-time card updates. Tailoring jobs use polling.

**Rationale**: Analysis is a synchronous user experience — they're watching cards sort in real time, so sub-second updates matter. Tailoring is a "kick off and leave" experience — the user may navigate away, so polling on return (or when they visit Tab 4) is sufficient and simpler to implement.

**Alternatives considered**: WebSockets for everything (more complex, overkill for tailoring). Polling for everything (too slow for the card-sorting UX).
