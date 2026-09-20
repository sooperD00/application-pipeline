# ADR-021: How Sprints Are Planned, Tracked and Closed

**Date**: 2026-09-19
**Status**: Accepted — the migration at the bottom landed 2026-09-20

**Decision**: A sprint is one file, identified by a hex ID that never changes. Order lives in exactly one place, `docs/sprints/plan.md`, and a sprint's status is the folder it sits in. Documents name a sprint or a leg by tag, source files carry cleanup markers and no other sprint reference, and a sprint closes by being moved with `git mv` rather than rewritten into a second document.

**Why**
- Separate files give a precise reading list for execution, and a tracked `git mv` for the archive.
- Hex IDs allow easy reordering in `plan.md` *and* stable references in source and docs.
- Sprint and leg sizing manages human and LLM attention during execution.
- Sprint and leg compartmentalized scope manages human and LLM context during execution.
- Phases manage product delivery expectations.

Anyone may do any step in this record, and everyone follows it whoever they are. Where a step is reserved, it says so.

## Vocabulary

| Term | Means |
|------|-------|
| **Phase** | A delivery milestone. The phases themselves live in [implementation-plan.md](../implementation-plan.md). |
| **Sprint** | One named change to the system, titled as the category of work. One file. |
| **Leg** | A sequenced segment of one journey, with an appetite of one sitting. |
| **Kind** | The commit-ordering heuristic for a leg. See the table below. |
| **Factor** | The class of thing a red suite would blame. |
| **Appetite** | One sitting per leg for a person, and a leg that fits the context of the model named in `plan.md`. |
| **Watch** | A known trap, written where the work is. |
| **Status** | planned → in progress → handed off → done YYYY-MM-DD, or dropped, with the reason. A sprint with no place in the order yet is parked. |
| **Housekeeping** | Work with no home yet, which can join any sprint. |
| **Tech debt** | Work deferred, probably for a while. |

| Kind | Ordering heuristic |
|------|--------------------|
| feature | import graph |
| migration | consumer graph |
| refactor | the suite is the invariant |
| upgrade | no graph — lock first, let the breakage name the commits |
| spike / investigation | planned as a sprint but quarantined in `test-vehicles/<spike-name>/` |
| bugfix | reproduce → fix → confirm (regression test) |

- Ask what orders the commits, not what the work is about. Deploy might be a migration, because dev → staging → prod is a consumer graph, or a feature, because the pipeline has to be built.
- Not every topic is a Kind. If nothing fits, discuss it before inventing one.

**Landed** — written when a leg or a sprint closes: what the plan said, what actually happened, and the lesson worth carrying. A leg's note sits under the leg. The sprint's note sits in the sprint file and travels with it. This is the note that makes the next plan better, which is the only reason planning gets less wrong over time.

**Checklist marks** — a box records what happened to an item, not only whether it is ticked. `[x]` done as written. `[ ]` open. `[-]` skipped in this sprint. `[~]` done anyway, against a call to skip or defer it. Neither `[-]` nor `[~]` ever stands alone: the prose beside it says *deferred to <place>* and why, or *not done because* and why. Deferring is a move rather than a note — the item reopens as `[ ]` in the place named, and takes an ID if that place is `housekeeping.md` or `techdebt.md`.

**Entry gate** — work in an *earlier* sprint that a later one leans on, named at the top of the sprint that needs it, as required or recommended. Never a second home: the gate line points at the leg that owns the work, and the spec stays there. A gate item with no owner is a missing sprint, not a checklist.

## Where things live

```
docs/sprints/
  plan.md                                        order, dependencies, completed log
  remaining/sprint-<id>-<short-name>.md          one planned or in-progress sprint
  completed/sprint-<NNN>-<id>-<short-name>.md    one finished sprint
  completed/phase-0-sprints-001-012.md           the Phase 0 archive, never split
  housekeeping.md                                unassigned work that can join any sprint
  techdebt.md                                    deferred work, probably for a while
docs/reading/reading-list-for-<id>-<leg>.txt     what one coding session was handed
```

- `plan.md` owns order, the dependency map, the completed log, and the model the appetite is sized against. It holds no sprint content.
- A sprint file owns everything about that sprint: why now, Kind, legs, done-when lists, commit tables, Watches, entry gates, Out of Scope, and Landed notes.
- Nothing owns status. The folder is the status: `remaining/` is not done, `completed/` is.
- Nothing outside `plan.md` stores a path to a sprint file, so a sprint that moves costs one line.

## IDs and file names

- Generate an ID with `openssl rand -hex 3` — six hex characters, e.g. `9cf8b9`.
- Roll again if all six come out digits, so an ID never reads as a number.
- Check it is unused with `git grep <id>` before writing it down.
- Name a planned sprint `sprint-<id>-<short-name>.md` and put it in `remaining/`.
- Name a finished sprint `sprint-<NNN>-<id>-<short-name>.md`, where `<NNN>` is the order it was actually done in, and put it in `completed/`.
- Give a sprint its file as soon as it has a name. A stub with an ID and a title is a legitimate sprint file; nothing has to be planned out to exist.
- Never renumber an ID, reuse one, or give a sprint a number that means its order.
- `9cf8b9` is the example ID used in documentation, here and anywhere else. Never assign it, so a grep for a real ID never lands in a worked example.

## Referring to a sprint

- Write `[s-<id>]` for a sprint and `[s-<id>-<leg>]` for a leg, in any document.
- Write `leg c` inside that sprint's own file, where there is nothing to confuse it with.
- Write `[SPRINT-<id>-CLEANUP]` or `[SPRINT-<id>-<leg>-CLEANUP]` in source, and name the sprint in words in the comment beside it.
- Cite an ADR, not a sprint, for why code is the way it is.
- Yes: `[s-9cf8b9]`, `[s-9cf8b9-c]`, `[h-4b2e07]`, `[t-88a1f3]`, `[SPRINT-9cf8b9-c-CLEANUP]`
- Never: `Sprint 19`, `19c`, a bare number, a sprint number in source outside a marker
- Sprints 1 through 12 predate this record. They are numbered, they live in one archive file, and references to them by number stay as they are. Don't write new ones.

## Tags in source

- Never write `TODO`, `FIXME`, `XXX` or `HACK`. A tag is how future work is named here, and a banned word is something a tool can check perfectly, which a convention about prose is not.
- `[SPRINT-<id>-<leg>-CLEANUP]` promises that this line changes or disappears at that leg. It expires, and the leg's done-when list proves it did.
- `[h-<id>]` or `[t-<id>]` says the work is filed, unscheduled, and this is where it would land. It describes what is true now; it does not instruct. Use it where the code location is part of the information — "auto-archive stale sessions" means less without the page it lives on.
- Promote when the work gets scheduled: an item that lands in a sprint takes that sprint's marker in source, and stops being a housekeeping reference.
- Keep every comment true in the present tense. A line that only makes sense as an instruction is scheduled work, and takes a marker.
- A tag in source is a cross-reference, never the record. The list holds the priority, the code holds the location, and the ID exists because the item is already filed.

## Plan a sprint

- Plan in a session of its own, separate from coding. Planning and coding compete for the same attention and the same context.
- Plan the next leg at the close of the one before it, so the plan meets the code as it actually landed rather than as it was imagined.
- Pick the Kind first, then cut the legs at factor boundaries, so one red suite has one cause.
- Size every leg to the Appetite. A leg that does not fit is two legs.
- Name the entry gates, each pointing at the leg that owns the work.
- Scan `housekeeping.md` for anything this sprint should absorb, and move it in.
- Add or update the sprint's row in `plan.md`.
- Generate the leg's reading list as the last step before its coding session.
- Enforce every rule in this record while planning. Whatever the plan gets wrong, the coding session inherits.
- Expect planning to be iterative: several sessions and tightenings, not one pass.
- Stop planning a leg when its done-when list can be checked by someone who did not write it, its entry gates name their owners, and its reading list exists. Those three are the test, and they are the whole test.
- Do not plan the decisions the code will make. Specify what constrains the work — interfaces, ordering, what must not move — and leave the rest to the keyboard. A sprint file nobody can hold in one head is over-specified, or it is two sprints.

## Reading lists

- Write one list per leg: `docs/reading/reading-list-for-<id>-<leg>.txt`.
- Keep the `.txt` extension. Prompt material is `.txt` here, and sessions are told not to read `.txt` unless a list is handed to them deliberately. Markdown formatting inside the file is fine.
- Generate it at the close of the preceding leg. A list written earlier describes a repo that no longer exists.
- Document a list only for the sprint in progress and for sprints already finished. Draft as many as you like anywhere else; they do not enter `docs/` until they are about to be used.
- Link it from `plan.md` with the date it was written. Where the row and the file disagree, the file wins.

## Run a sprint

- Run one leg at a time. The leg is already sized for the model named in `plan.md`.
- Go back to planning when the plan is wrong or does not fit. Re-planning is cheaper than a leg that lands wrong.
- Update the sprint file as the work moves — plans, items, gates, closing tasks — and let the commits carry the history. Do not narrate a superseded plan inside the file; the diff already says what changed.
- Place a cleanup marker the moment you leave something for later, naming the leg that will remove it. If no leg owns it yet, file it in `housekeeping.md` or `techdebt.md` and cite that ID instead — never leave the comment as the only record.
- Add a Watch when you hit a trap, where the work is.

Two kinds of prompt get confused, so they are named here. **App prompts** ship in the backend and go to the Claude API while the application runs; they are in this repo, and getting them out of it is tracked in `techdebt.md`. **Dev prompts** are assembled by hand from private templates to build this application; they are IP, they live in the private `<this-repo-name>-devlog` repo, and nothing here reproduces them. The planning artifacts that *are* public are the sprint files, `plan.md`, and the reading lists.

## Hand off a leg

- Check the leg's done-when list item by item, at the code rather than at the plan.
- Write the leg's Landed line.
- Record the leg's handoff date.
- File what the leg shed: housekeeping items in `housekeeping.md`, tech debt in `techdebt.md`, each with a generated ID.
- Confirm no cleanup marker naming this leg is left in the repo.
- Update the docs the leg changed, tags and references included.
- Leave the sprint file where it is. Nothing moves until the whole sprint closes.

## Hand off a sprint

- Confirm every leg is handed off, and that `git grep 'SPRINT-<id>'` returns nothing.
- Record the sprint's handoff date.
- Report the housekeeping count. Past ~50 unassigned items, stop and spend a planning session: assign them into sprints, defer them to `techdebt.md`, or plan a cleanup sprint. A list nobody can hold is a list nobody reads.

## Close a sprint — reserved to the maintainer

- Review the work, then close and tag it. A handoff is not a close.
- Move the file with `git mv`, never a copy-paste, so its history and its Landed notes travel with it.
- Add the `<NNN>` execution-order prefix in the same move: `remaining/sprint-<id>-<name>.md` becomes `completed/sprint-<NNN>-<id>-<name>.md`.
- Add the sprint's row to the completed log in `plan.md`.
- Push the branch before the tag. A tag pointing at a commit nobody has is a tag nobody can check out.
- Tag it `sprint-<NNN>-<id>`, which is the file name without its short name — so one grep finds the file, its row in the completed log, and the tag.

## Three clocks, on purpose

- **handoff** — the work came back. Recorded on the leg and on the sprint, in the sprint file.
- **commit** — git author dates. When the code was reviewed and blessed, atomically.
- **tag** — `sprint-<NNN>-<id>`. The sprint closed: code blessed, docs passed, next sprint planned.

Do not reconcile these against each other or against `git log`. They measure different events, and a sprint handed off one week and closed the next is a fact worth keeping, not a discrepancy to fix.

## Order and re-order

- `plan.md` holds one table: `NNN | id | name | status | depends on | reading list`.
- Leave `NNN` blank until the sprint closes. It records the order things were actually done in, not the order they were planned in.
- Put `[s-<id>]` tags in **depends on**. Anything not named there may be reordered freely, which is the reason to write the column at all.
- Treat **status** as a convenience copy for reading the table at a glance. The folder is the truth, and a linter can check the two agree.
- Link the leg's reading list with the date it was written. The file wins where they disagree.
- Re-order by editing this table. No sprint file changes when the order changes, which is the whole reason the ID is not the order.
- Tighten the plan at every leg close: the order, the gates, and the next leg's reading list.

## Housekeeping and tech debt

- Record an item with a generated ID in `housekeeping.md` as `[h-<id>]`, or in `techdebt.md` as `[t-<id>]` when it is deferred rather than merely unassigned.
- Assigning an item to a sprint is optional. If you assign it, write it into that sprint's file as an ordinary item and give it no tracker ID — the sprint is its home. If you do not, it gets the hex ID and waits.
- Never guess a destination. An item filed into the wrong sprint is worse than an item sitting in housekeeping, because the wrong sprint inherits it silently.
- Keep the dated provenance line when an item moves, the way "(Pulled from Housekeeping, 2026-09-17)" reads today.
- Nothing renumbers these lists. The count is reported, not maintained.
- Source may cite an `[h-` or `[t-` item, under the rules in Tags in source. What it may not do is be the only record: the ID exists because the item is in a list, and the day it gets a sprint the reference becomes that sprint's marker.

**Consequences**
- `plan.md` becomes the single point of failure. If it drifts, nothing resolves.
- Overhead managing the extra files.
- Linting and script maintenance, now its own item in the developer tooling sprint.
- A sprint file has to stand alone, because it is what gets handed to a coding session along with its reading list.

**Alternatives considered**
- **Numbers that mean order.** What this replaces. Inserting one sprint cost 117 edits across four documents on 2026-09-19, and no regex can tell a bare sprint number from a test count.
- **One long plan document.** Cheap to grep, but it hands a reader 1,180 lines to use 200 of them, and closing a sprint means copy-pasting it into a second long document.
- **A file per leg.** Too fine. Legs are planned and read together, and the appetite rule already caps a leg at one sitting.

## Migration — done 2026-09-20

1. Create `docs/sprints/` with `remaining/` and `completed/`.
2. Generate an ID per sprint and split `remaining-sprints.md` into one file each, content verbatim, verified line for line.
3. `git mv` `completed-sprints.md` to `completed/phase-0-sprints-001-012.md`. The execution-order counter continues at 013.
4. Move Housekeeping and Tech Debt into `housekeeping.md` and `techdebt.md`, with IDs replacing `H-n` and `T-n`.
5. Write `plan.md`: the table, the completed log, the model, and a link to this record.
6. Convert prose references to tags, and the six source markers to IDs.
7. Point `README.md` and the other docs at `docs/sprints/plan.md`.
