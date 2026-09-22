# Sprint Plan

How all of this works — the vocabulary, the rules, and what to do at each step — is
[ADR-021](../decisions/adr-021-planning-system.md). Read that once; this file is the live state.
Work with no sprint yet waits in [housekeeping.md](housekeeping.md), and deferred work in
[techdebt.md](techdebt.md).

LLM MODEL = Claude Opus 5 Max Thinking

## Phases

Delivery milestones, each designed in [implementation-plan.md](../implementation-plan.md).
Phase 0 is deployed; Phase 1 is in progress.

- [Phase 0 — "Replace My Excel Workflow"](../implementation-plan.md#phase-0--replace-my-excel-workflow)
- [Phase 1 — "My Brother Can Use It Too"](../implementation-plan.md#phase-1--my-brother-can-use-it-too)
- [Phase 2 — "It's a Product"](../implementation-plan.md#phase-2--its-a-product)
- [Phase 3 — "People Pay For This"](../implementation-plan.md#phase-3--people-pay-for-this)
- [Phase 4 — "Polish and Grow"](../implementation-plan.md#phase-4--polish-and-grow)

## Order

Top-down. `NNN` stays empty until a sprint closes, and then records the order it was actually
done in. Re-order by moving a row: no sprint file changes when the order does.

| NNN | id | name | status | depends on | reading list |
|-----|----|------|--------|------------|--------------|
| | `[s-a75ff1]` | [Backend dependencies](remaining/sprint-a75ff1-backend-dependencies.md) | in progress | — | — |
| | `[s-41441e]` | [Tests](remaining/sprint-41441e-tests.md) | planned | `[s-a75ff1]` | — |
| | `[s-07579b]` | [Consolidating Railway services into one project](remaining/sprint-07579b-railway-consolidation.md) | planned | — | — |
| | `[s-26be17]` | [Code hygiene](remaining/sprint-26be17-code-hygiene.md) | planned | — | — |
| | `[s-3f291c]` | [Developer tooling](remaining/sprint-3f291c-developer-tooling.md) | planned | `[s-a75ff1]`, `[s-41441e]` | — |
| | `[s-17c7e9]` | [Custom domain](remaining/sprint-17c7e9-custom-domain.md) | planned | — | — |
| | `[s-26220f]` | [User authentication](remaining/sprint-26220f-user-authentication.md) | planned | `[s-41441e]`, `[s-17c7e9]` | — |
| | `[s-2716d1]` | [Billing](remaining/sprint-2716d1-billing.md) | planned | `[s-26220f]`, `[s-07579b]` | — |
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
| 013 | `[s-603d20]` | [Adopt ADR-021 across the repo](completed/sprint-013-603d20-adopt-adr-021.md) | 2026-09-20 |

The counter continues at 014.
