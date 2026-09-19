# ADR-012: Split cover_letter and app_answers Into Separate Templates

**Date**: 2026-03-05
**Status**: Accepted

**Decision**: The `cover_letter_app_answers` PromptPhase is split into two separate phases: `cover_letter` and `app_answers`. Each gets its own PromptTemplate row, its own editable text box in the UI, and independent toggle conditions.

**Rationale**: Cover letters and application answers have different activation conditions already modeled in the data: `jd.cover_letter_requested` gates cover letters, `jd.app_questions` being populated gates app answers. Combining them in one template forces awkward partial-inclusion logic and prevents users from reading and editing them independently. The separation also means Claude's response JSON has separate fields for each, making parsing unambiguous.

**Migration note**: The Postgres enum retains the old `cover_letter_app_answers` value (can't DROP VALUE from a Postgres enum) but it is no longer referenced in application code.

**Alternatives considered**: Keep combined (simpler schema, but wrong separation of concerns for both the UI and the conditional logic).
