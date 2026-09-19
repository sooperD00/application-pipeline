# ADR-003: Claude Opus as Default Model

**Date**: 2026-02-28  
**Status**: Accepted

**Decision**: Use `claude-opus-4-6` for all API calls by default. Model is a config value, not hardcoded.

**Rationale**: The batch analysis phase benefits significantly from extended thinking and cross-JD reasoning. Resume tailoring quality directly impacts callback rates — this is the core value proposition and not the place to save pennies. Actual costs will be tracked from day one; pricing will be set after real data is in.

**Alternatives considered**: Sonnet for batch analysis (cheaper, possibly sufficient for simple fit/no-fit, but loses the strategic meta-analysis quality). Hybrid approach (Opus for analysis, Sonnet for tailoring) remains an option if costs are too high.
