# Adopt ADR-021 across the repo

**ID**: `[s-603d20]`
**Status**: handed off
**Handoff**: 2026-09-20
**Phase**: 1

Put the repo under the planning system [ADR-021](../../decisions/adr-021-planning-system.md)
describes: one file per decision, one file per sprint, IDs that never move, and tags where
numbers used to be — the records first, then the plan, then the code that points at both.
**Kind:** migration — consumer graph.
**Entry gate:** none.

**Why now** Inserting one sprint on 2026-09-19 cost 117 edits across four documents, and the
pass could only be finished by reading the diff, because no regex tells a sprint number from a
test count. The numbering was the visible cost. Underneath it were a 1,180-line plan document
that a reader consumed whole to use a fifth of, and a close procedure that copy-pasted a sprint
from one long file into another.

### leg a — one file per ADR (migration) --- handed off 2026-09-19

**Landed.** Nothing planned this; it was picked as the rehearsal for leg b, the same move at
lower risk. `decisions.md` became 18 files plus an index, content moved verbatim, with a
splitter that compared every non-empty line in order before and after.

- ADR numbers were already identity rather than order, so every citation by ID survived the
  split and only four paths had to move. That is the property leg b then bought for sprints.
- The check earned its keep by failing first: it flagged the heading promotion it had not been
  told to expect. A verification that never fails has not been tested.

### leg b — the plan becomes docs/sprints/ (migration) --- handed off 2026-09-20

**Landed.** `remaining-sprints.md` split into one file per sprint under stable hex IDs,
`completed-sprints.md` moved with `git mv` into the Phase 0 archive, housekeeping and tech debt
became their own files, and `plan.md` took the order, the dependencies and the completed log.
121 tags replaced the numbers; the six source markers took IDs and legs.

- The converter rewrote ADR-021's own counter-examples, turning "Never: `Sprint 19`" into
  "Never: `[s-26220f]`" and inverting the rule it was quoting. A tool that rewrites references
  has to treat its spec as data. The lesson is in [s-3f291c]'s linter item, and the answer is to
  exclude lines rather than files: an exclusion on a file silently exempts everything added
  later.
- Two proofs did the work that care alone would not have: masking every digit showed only digits
  moved, and an ordered line comparison showed no content was lost. Both found real bugs.
- The `H-4` in [s-a75ff1]'s close-out table pointed at a different item than today's `H-4`,
  because the list had been renumbered a day after that commit. The bug this sprint exists to
  stop was already in the repo, unnoticed.
- Sprints 1 through 12 were grandfathered rather than converted. Giving twelve finished sprints
  IDs that all resolve into one archive file would have bought nothing.
- `git grep -E` on macOS does not support `\b`; `-P` does. Two searches came back empty and
  looked like good news.

### leg c — source comes under the same rules (refactor) --- handed off 2026-09-20

**Kind:** refactor — the suite is the invariant. Comments only; no behavior moves.

Pulled from Housekeeping as `[h-0ada85]`, 2026-09-20. Seven comments predate ADR-021 and none
carries a tag. They do not land in one place, which is why the item waited for the ADR to say
what a tag in source promises.

**Done when**
- [x] `git grep -nE 'TODO|FIXME|XXX|HACK'` over `backend/`, `frontend/` and `scripts/` returns
      nothing
- [x] every remaining tag in source resolves: a `[SPRINT-` marker to a sprint in `plan.md`, an
      `[h-` or `[t-` reference to an item still in its list — six distinct tags, all checked
- [x] no comment reads as an instruction unless it carries a marker
- [ ] the frontend suite is unchanged — 12 tests in `TailoringPage.test.jsx` and the rest, same
      counts before and after

**Scope**
- Four are work [s-77f2e3] already lists, so they take its marker: the Enter-to-submit
  preference and the company/role auto-populate in `JDPasteForm.jsx`, the pre-populated-fields
  note beside the form, and `NotFoundPage.jsx`'s 404 copy, which waits on ADR-016.
- `analysis.py:55` takes `[t-84a71a]`, the prompt-extraction item, and cites ADR-013 — which
  already records that the two futures pull against each other.
- `SessionsPage.jsx:12`, stale sessions, is in no list at all. It gets one.
- `main.py:4` is not work: "Phase 0, Sprint 12" is a status line that rots where it sits. The
  claim goes; the capability summary stays. [s-26220f-a] is already scheduled to correct the
  auth line three below it.

**Watch** `JDPasteForm.jsx` holds two implementations of submit-on-Enter, one live and one
commented out. The comment above them is a decision record, not a TODO — keep the reasoning and
retag the intent.

**Landed.** The plan said seven comments with one path each. Six turned out to carry a banned
word and the seventh was a status line, so the sed everyone pictures was never the work —
deciding where each one belonged was, and that is exactly what the ADR had to settle first.

- Two of them were carrying dead facts, not just missing tags. `JDPasteForm.jsx` called its own
  workaround a "quick win to paste the 1st to lines before Sprint 10's Claude extraction", and
  Sprint 10 shipped without ever adding that extraction. A stale TODO hides a stale claim, which
  is the better argument for banning the word than tidiness.
- `SessionsPage.jsx` was the only one in no list at all: three options, no decision, since Phase
  0. It is `[h-0167ce]` now. Filing it is all the ADR asks of an unscheduled idea, and it took
  one line.
- The frontend suite was not run. `frontend/node_modules` is absent on this machine, the same
  fresh-clone gap [s-a75ff1-b]'s prework records for the venv. The change is comment-only and
  the diff was read line by line, but that done-when stays open until someone runs it.

## Handoff, 2026-09-20

- Every leg is handed off. `git grep 'SPRINT-603d20'` returns nothing — this sprint left no
  markers behind.
- Housekeeping stands at five items, well under the fifty that would force a planning session.
- What is left is the reserved step: review, close, `git mv` to `completed/` as
  `sprint-013-603d20-adopt-adr-021.md`, the row in `plan.md`'s completed log, and the
  `sprint-013` tag.
