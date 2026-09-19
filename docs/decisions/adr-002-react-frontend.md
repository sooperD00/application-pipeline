# ADR-002: React over Vue / Streamlit / FastHTML

**Date**: 2026-02-28  
**Status**: Accepted

**Decision**: React (via Vite) for the frontend.

**Rationale**: Three factors — (1) portfolio value: React appears in the majority of frontend-requiring JDs, having a real project in it is a career asset; (2) ecosystem: the card animation UI and SSE consumption have well-supported React libraries; (3) the UI has enough interactive complexity (fanned cards, drag-to-reorder, live status updates, tabbed views with background processing) that a framework designed for rich interactivity is warranted.

**Alternatives considered**: Vue (easier learning curve, smaller ecosystem), Streamlit (fast to prototype but fights you on custom layouts), FastHTML (Python-native but immature, limited component ecosystem).
