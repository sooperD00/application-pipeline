# Tests

**ID**: `[s-41441e]`
**Status**: planned
**Phase**: 1
<!-- was Sprint 14 before ADR-021 -->

**Legs:** fix the red suite (bugfix), then fill the gaps (feature).
**Entry gate:** [s-a75ff1-c] required before leg a. Its done-when compares test counts against
the [s-a75ff1-a] baseline, 18 failures included, and leg a here changes them (verified in a
scratch copy: 88 passed → 106 passed).

Fill concrete gaps. The goal is confidence before auth ([s-26220f]), and before CI, which can't
live on a red suite.

## leg a — restore a green suite (bugfix) --- planned

`tests/test_tailoring.py` has 18 failing tests with one cause, session/DB wiring. They predate
[s-a75ff1] and were not fixable inside it — the [s-a75ff1-a] baseline recorded the same 18 before and
after the migration. Until they are green, every "test counts unchanged" done-when in this doc
is measuring a suite that is already red. (Pulled out of Housekeeping, where it was marked for
[s-a75ff1] — the wrong sprint.)

**Done when**
- [ ] the 18 failures pass, and nothing else changes: 0 failed, same collected count
- [ ] the `client` fixture's comment says what the override does, and its
      `[SPRINT-41441e-a-CLEANUP]` marker is gone

**Commits**
| # | | |
|---|---|---|
| 0 | reproduce | Run pytest. `test_list_sessions: assert 0 == 2` is the tell: every request runs as a fresh anonymous user instead of `seeded_user` (artifact, not a commit) |
| 1 | fix | In the `client` fixture, add `app.dependency_overrides[get_current_user] = lambda: seeded_user` beside the `get_session` override, and rewrite the marked comment above it |

## leg b — fill the gaps (feature) --- planned

Backend — new file:
- `test_jds.py`: zip package download (ADR-014), docx download, JD CRUD (PATCH fields, status
  override), single-JD tailoring kickoff. Currently only tested indirectly through
  session-level tests.

Frontend — extend existing:
- `TailoringPage.test.jsx`: polling lifecycle test (advance fake timers, assert
  queued→processing→ready transition updates UI). Highest-complexity React test pattern — fake
  timers + async state + `act()` wrapping. Currently 12 tests cover rendering and button clicks
  but not the polling state machine.

**Also in scope**
- [ ] Confirm the frontend suite is unchanged after [s-603d20]'s comment-only pass — 12 tests in
      `TailoringPage.test.jsx` and the rest, same counts before and after. That sprint closed
      without running it because `frontend/node_modules` is absent on this Mac, which belongs to
      the machine migration rather than to a docs sprint. (Deferred from [s-603d20-c],
      2026-09-20.)
- [ ] Extract shared test factories and mocks — `__tests__/factories.js` and `__tests__/mocks.js`
      — but only if the same factory or mock has turned up in 3+ test files with an identical
      shape by the time you are in there. Data models have to stabilize first, and this sprint
      is when you find out whether they have.

**Moved out, 2026-09-17.** Three items left this sprint for one that owns them better.
`test_analysis.py` and the six `failed`-path tests in `test_tailoring.py` went to [s-2716d1-a], which
puts the spend paths under test in the sprint where money starts touching them. The
ownership/auth guard test ("session belongs to a different user") went to [s-26220f-d], where the guard
it tests actually exists — writing it here would have tested a stub.
