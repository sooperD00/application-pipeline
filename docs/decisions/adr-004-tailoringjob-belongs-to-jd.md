# ADR-004: TailoringJob Belongs to JD, Not Session

**Date**: 2026-02-28  
**Status**: Accepted

**Decision**: TailoringJob has a foreign key to JD, not to Session.

**Rationale**: Tailoring jobs outlive their session context. Interview prep happens days or weeks after the session. A user's interaction with a tailored application (reviewing, editing, continuing for interview prep) is JD-centric, not session-centric. Session-based ownership would require joining through Session → JD → TailoringJob for every interview prep query. Limit enforcement (free tier caps) can query by user through JD → Session → User.

**Alternatives considered**: Nesting under Session (simpler conceptual model but wrong ownership for the interview prep lifecycle).
