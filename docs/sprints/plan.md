# Sprint Plan

How all of this works — the vocabulary, the rules, and what to do at each step — is
[ADR-021](../decisions/adr-021-planning-system.md). Read that once; this file is the live state.

LLM MODEL = Claude Opus 5 Max Thinking

## Order

Top-down. `NNN` stays empty until a sprint closes, and then records the order it was actually
done in. Re-order by moving a row: no sprint file changes when the order does.

| NNN | id | name | status | depends on | reading list |
|-----|----|------|--------|------------|--------------|
| | `[s-603d20]` | [Adopt ADR-021 across the repo](remaining/sprint-603d20-adopt-adr-021.md) | in progress | — | — |
| | `[s-a75ff1]` | [Backend dependencies](remaining/sprint-a75ff1-backend-dependencies.md) | in progress | — | — |
| | `[s-41441e]` | [Tests](remaining/sprint-41441e-tests.md) | planned | — | — |
| | `[s-07579b]` | [Consolidating Railway services into one project](remaining/sprint-07579b-railway-consolidation.md) | planned | — | — |
| | `[s-26be17]` | [Code hygiene](remaining/sprint-26be17-code-hygiene.md) | planned | — | — |
| | `[s-3f291c]` | [Developer tooling](remaining/sprint-3f291c-developer-tooling.md) | planned | `[s-a75ff1]`, `[s-41441e]` | — |
| | `[s-17c7e9]` | [Custom domain](remaining/sprint-17c7e9-custom-domain.md) | planned | — | — |
| | `[s-26220f]` | [User authentication](remaining/sprint-26220f-user-authentication.md) | planned | `[s-41441e]`, `[s-17c7e9]` | — |
| | `[s-2716d1]` | [Billing](remaining/sprint-2716d1-billing.md) | planned | `[s-26220f]` | — |
| | `[s-77f2e3]` | [Frontend polish](remaining/sprint-77f2e3-frontend-polish.md) | parked | — | — |

**depends on** names required entry gates only. Each sprint file carries the full gate line,
recommended gates included, pointing at the leg that owns the work. Anything not named here may
be reordered freely.

Whatever a `[SPRINT-<id>-CLEANUP]` marker names has to exist in this table — which is why a
parked sprint still gets a row and an ID.

No reading lists yet: the first one belongs to the next leg that runs.

## Completed

| NNN | id | name | handoff |
|-----|----|------|---------|
| 001–012 | — | [Phase 0 — Sprints 1 to 12](completed/phase-0-sprints-001-012.md) | dates in the file |

The counter continues at 013.

## Phase 1

Phase 0 is deployed. Phase 1 delivers auth, billing and onboarding, plus the tracking and
metrics that make the funnel visible to the user and to me. The deliverables are designed in
[implementation-plan.md, Phase 1](../implementation-plan.md#phase-1--my-brother-can-use-it-too);
the sprint order that gets there lives here. Where Phase 1 ends is not decided yet.

**Delivering in Phase 1**

- Auth, billing, user onboarding
- Tracking table and metrics for the user
- Tracking and metrics for the app and the dev — cost per session and per user, funnel data,
  error visibility
- Per-user cost caps and rate limiting — my API key pays for every beta session today, and
  billing needs metering anyway
- Data lifecycle — anonymous retention and anonymous → account conversion land in [s-26220f]. A
  delete-my-data path is deferred to public release ([s-26220f]'s Out of Scope), which is the honest
  place for it: it is a promise to keep, not a feature to ship early and half-wire
- Terms of service and a privacy policy — due with [s-2716d1-d]'s go-live commit, which publishes the
  public page Stripe's activation review reads
- Job durability — BackgroundTasks die with the request; architecture.md routes this to
  arq/Redis once users are concurrent
- Railway database backups — [s-2716d1]'s entry gate, since the credit ledger holds paid balances
- Suite health, and whatever tooling this phase warrants for quality and maintainability
