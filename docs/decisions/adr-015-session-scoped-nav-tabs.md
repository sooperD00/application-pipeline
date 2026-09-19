# ADR-015: Session-Scoped Nav Tabs Visible at All Times (Grayed When Inactive)

**Date**: 2026-03-09  
**Status**: Accepted

**Decision**: The top nav always shows all five workflow tabs — Scrape & Analyze, Calibrate, Review & Enrich, Tailoring, Resumes — regardless of whether a session is selected. Session-scoped tabs (Calibrate, Review & Enrich, Tailoring) render grayed out / disabled when no session is active. Clicking a disabled tab shows a tooltip: "Select or create a session to unlock this step."

**Rationale**: The tab bar *is* the product story. A first-time visitor (or a hiring manager watching a demo) should see the full workflow — paste, analyze, calibrate, review, tailor — without having to start a session to discover what happens after step one. Five tabs is well within comfortable horizontal nav density; clutter becomes a real concern around 8+. The 2:3 active-to-disabled ratio when no session is selected reads as "there's more to unlock," not "this app is broken." This is the checklist principle: the user reads the whole pipeline before starting it, which sets expectations for the session-as-a-unit-of-work model (ADR-006).

**Alternatives considered**: Show session-scoped tabs only after entering a session (cleaner layout, but hides the product's feature surface from new users and breaks the mental model of "session = these five steps"). Dynamic nav was the more conventional UX choice, but this app doubles as a portfolio piece and a potential product — discoverability wins over minimalism here.
