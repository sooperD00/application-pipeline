# ADR-016: Entity Lifecycle and Route Hierarchy (Phase ?)

**Date**: 2026-03-11  
**Status**: Accepted

**Decision:** JDs graduate from session-scoped to independent entities; /sessions is the funnel, /tracking becomes index, /pursuits/:jd_id owns post-callback workflows. Context: the manual workflow folder structure, the 500→100→5 funnel, and the fact that session context is captured as data on the JD, not a route dependency.
