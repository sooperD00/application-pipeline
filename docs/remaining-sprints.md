# Remaining Sprints

LLM MODEL = Claude Opus 5 Max Thinking

TERMINOLOGY
> Execution order: top-down. Next sprint is at the top.
> "Phase" = a delivery milestone (see [implementation-plan.md](implementation-plan.md) Phases).
> "Sprint" = one named change to the system, titled as the category of work.
> "Kind" = commit-ordering heuristic for a leg. [feature | refactor | migration | upgrade]
> "Leg" = sequenced segment of one journey, with an appetite of one sitting
> "Factor" = the class of thing a red suite would blame.
> "Appetite" = sizing rule of one sitting per leg (human); fits in [LLM MODEL] context.
> "Watch" = a known trap.
> "Status" = planned → in progress → done YYYY-MM-DD, or dropped (say why).
> "Landed" = written when a sprint or leg closes: what the plan said, what actually happened,
>   and the lesson worth carrying. A leg lands under itself here; a whole sprint lands in
>   completed-sprints.md once every leg is done.
> "Housekeeping" = can be added to any sprint; "Tech Debt" = deferred, probably for a while.
> `[SPRINT-<N>-CLEANUP]` = a grep marker naming the sprint that will clean this up. Placed in
>   source files and in this doc during planning or coding, so that every TODO carries an
>   intended when. `<N>` is always a real sprint number, even if it moves later. Unplanned work
>   gets no marker and does not belong in source — it goes to Housekeeping or Tech Debt here.
> "H-n" / "T-n" = ID for one *unassigned* Housekeeping or Tech Debt item. This doc only: source
>   never references them, because anything source points at is planned and carries a
>   `[SPRINT-<N>-CLEANUP]` marker instead. Renumbered 1..N on a docs pass, so the count is the
>   signal — past ~50 unassigned, hold a planning session before adding features.


> "Kind" map to a distinct ordering heuristic:

| kind      | ordering heuristic |
|-----------|--------------------|
| feature   | import graph |
| migration | consumer graph |
| refactor  | the suite is the invariant |
| upgrade   | no graph — lock first, let the breakage name the commits |
| spike / investigation    | planned as a sprint but quarantined in `test-vehicles/spike-name/` (repo root) |
| bugfix    | reproduce → fix → confirm (regression test) |

> tell me if you need another "Kind" -- we can discuss.
Not every topic is a Kind. Ask what orders the commits, not what the work is about
    - deploy might be a migration: dev → staging → prod is a consumer graph
    - deploy might be a feature: build the pipeline

---

## Phase 1 Overview

Phase 0 is deployed. Phase 1 delivers auth, billing and onboarding, plus the tracking and
metrics that make the funnel visible to the user and to me. The deliverables are designed in
[implementation-plan.md, Phase 1](implementation-plan.md#phase-1--my-brother-can-use-it-too);
the sprint order that gets there lives here. Where Phase 1 ends is not decided yet.

**Delivering in Phase 1**

- Auth, billing, user onboarding
- Tracking table and metrics for the user
- Tracking and metrics for the app and the dev — cost per session and per user, funnel data,
  error visibility
- Per-user cost caps and rate limiting — my API key pays for every beta session today, and
  billing needs metering anyway
- Data lifecycle — anonymous retention, anonymous → account conversion, and a delete-my-data
  path, since this holds other people's resumes
- Terms of service and a privacy policy, paired with that deletion path, before money moves
- Job durability — BackgroundTasks die with the request; architecture.md routes this to
  arq/Redis once users are concurrent
- The ADR-013 prompt-extraction decision, before public traffic rather than after
- Railway database backups
- Suite health, and whatever tooling this phase warrants for quality and maintainability

**Sprints**

- 13 — Backend dependencies, pip → uv — in progress (13a done, 13b/13c/13d planned)
- 14 — Tests — planned
- 15 — Developer tooling — planned
- 16 — Auth, magic link accounts — planned
- 17 — Billing — planned

Numbers are expectations, not commitments: they can be bumped, split or dropped. The one rule
is that whatever a `[SPRINT-<N>-CLEANUP]` marker names has to exist in this list.

---

## Sprint 13 — Backend dependencies --- in progress

Migrate backend dependency management from pip to uv.
**Kind:** migration
**Legs:** migration, consumer flip, version upgrade — the first two move packaging (factor 1) with versions pinned; the third moves versions (factor 2) with packaging fixed. Merging the last two means a red suite can't say which.

**Why now** CE! (Copy Exactly!, the Intel sense — match the current SWE standard rather than
invent a local one). Also: requirements.txt is a pip freeze —
13 real roots buried in 20 transitives, hand-appended since. Nothing declares what this
project actually requires, so nothing can be upgraded deliberately.

### 13a — requirements.txt → uv (migration) --- done 2026-09-16

**Done when**
- [x] `uv pip freeze` matches the pre-migration `pip freeze` exactly — same packages,
      same versions, against the commit-0 artifact
- [x] pytest collected count and pass/skip counts are unchanged — 106 collected, 88 passed,
      18 failed before and after, and the same 18 (`docs/DEVLOG/sprints/sprint13/`)
- [x] `uv lock --check` and `uv sync --check` both exit clean
- [x] `docker build` still succeeds — this leg must not touch prod

**Commits**
| # | | |
|---|---|---|
| 0 | ground truth | `pip freeze` + test counts captured before anything moves (artifact, not a commit) |
| 1 | new beside old | pyproject: `[project]` names, `[dependency-groups]`, constraint-dependencies, `package = false` |
| 2 | prove equivalence | freeze diff empty, test counts match |
| 3 | guard the venv | `.dockerignore` excludes `backend/.venv` |
| 4 | shim the consumer | requirements.txt becomes `uv export` output — same file, new status: generated |

**Close-out (unplanned), 2026-09-16.** A "stash" commit (673f7a0) put a first .gitignore/.dockerignore
overlap check on main. It moved start.sh, so the Railway deploy failed, and its new workflow failed on
every push. Reverted in fe8794e (deploy green again). Then:

| commit | |
|---|---|
| 0a8cbde | doc conflicts fixed (prompts location, H-4, spike location, README) |
| 0a57dc5 | `check_docker_context.py`: lists files git ignores that Docker would still get |
| ea7213e | `.dockerignore` covers every rule git ignores (probe: 398 leaks → 0; tracked build context unchanged) |
| df7ad46 | the check also sees files inside ignored nested git repos |
| c1755c8 | check moved to `scripts/`; README Quick Start → Checks says when to run it |
| 47a2b07 | sprint13 freeze paths point at `docs/DEVLOG/sprints/sprint13/` |

The first attempt is parked in `test-vehicles/dockerignore-check/`. It sat on branch
`idea/dockerignore-check` until the same day, when the branch was folded into main and deleted.

**Landed.** Plan: four commits plus a ground-truth artifact. Actual: five, then eleven more.

- The freeze tooling (`fc481a7`) landed first and was never in the table. "Prove equivalence"
  was planned as commit 2, but it is a test run, not a commit — the tooling that makes the run
  possible is the thing that gets committed. Plan the tooling as commit 1 next time.
- Planned commit 1 became two: `bf3cd00` (pyproject) and `5e8a730` (uv.lock). Declaring the
  roots and pinning the resolution are separate reviewable steps, and reading them together
  hides which one moved a version.
- "This leg must not touch prod" is not achievable as written. Every push to main deploys to
  Railway, which is exactly how `673f7a0` broke it. The honest done-when is "must not change
  what prod runs" — write that, and a stash commit reads as the violation it is.
- A "stash" commit on main is live: CI and Railway both run it. Park inert ideas in
  `test-vehicles/`, and use a short-lived branch only for changes that must sit in their real
  location (workflows, root configs, app code).
- What held: the counts. 106 collected, 88 passed, 18 failed, identical lists before and
  after, captured on the Windows machine into `docs/DEVLOG/sprints/sprint13/`.

**Close items**

- [x] Delete `backend/venv`, the pre-migration pip venv — done 2026-09-17, by hand on the
      Windows machine, since it is untracked and no fetch or checkout would remove it. Safe
      once 13a closed: the baseline freeze is captured in `docs/DEVLOG/sprints/sprint13/` and
      pushed to the devlog repo, `compare` reads files rather than environments, and neither
      13b nor 13c consumes the old venv. (Was H-1.)
- [ ] Add `.gitattributes` with `* text=auto eol=lf`, then `git add --renormalize .`, as its
      own commit so it reverts cleanly. 29 tracked files are CRLF in the index today —
      LICENSE, `config.py`, `database.py`, `alembic/env.py`, `pyproject.toml`, `.env.example`
      and everything under `docs/design/` and `docs/feedback/` — against 87 LF, with no
      `.gitattributes` at all. That mix is why `dep_freeze.py` carries CRLF-preserving read and
      write helpers. Renormalizing keeps either machine usable and stops generated files
      re-diffing on line endings alone. (Was T-2, which only saw the requirements.txt symptom.)

### 13b — flip the consumers, delete requirements.txt (consumer flip) --- planned

**Prework (before the first `uv sync` on a machine)**

uv picks its environment from the directory you run it in and never says which one it picked.
That cost an hour in 13a, when a stale root `.venv` answered instead of `backend/.venv`.

- Run uv from `backend/`. From anywhere else, `uv --directory backend run ...`.
- Check before trusting any number: `uv run python -c "import sys; print(sys.prefix)"` has to
  end in `backend/.venv`.
- There is exactly one `.venv` and it lives in `backend/`. A `.venv` at the repo root is the
  bug, not a second option — delete it rather than working around it.
- Repo-root `scripts/` is stdlib-only by design and needs no venv. Keep it that way: the
  context check has to run exactly when the environment is in doubt.
- This Mac has neither venv yet, being a fresh clone. Sprint 15's Makefile is the planned
  guard (a preflight target that fails unless `sys.prefix` ends in `backend/.venv`).

**Done when**
- [ ] `docker build` succeeds installing from pyproject + uv.lock, with no requirements.txt in the repo
- [ ] the built image runs migrations and starts uvicorn
- [ ] image size is same or smaller — compare against a build from `da59650` or later, see H-4
- [ ] `python3 scripts/check_docker_context.py --probe` exits 0 (13b edits the Dockerfile and `.dockerignore`)
- [ ] `git ls-files --error-unmatch backend/requirements.txt` fails — the file is out of the index
- [ ] `git grep -n requirements.txt -- ':!docs' ':!test-vehicles'` returns nothing. Use `git
      grep`, which reads tracked files only: a plain `grep -rn .` also reads `.git/`, where
      13b's own delete-commit message will match, plus `backend/.venv` and
      `frontend/node_modules` once those exist. Tracked references to clear: `Dockerfile`
      (COPY and pip install), `.dockerignore` (the venv comment), and `README.md` (Quick Start
      and the repo tree).

**Commits**
| # | | |
|---|---|---|
| 1 | flip consumer | Dockerfile installs from the lock, dev group excluded |
| 2 | flip consumer | README local-setup section |
| 3 | delete the old | `git rm backend/requirements.txt` |

**Watch** start.sh calls bare `alembic` and `uvicorn` off PATH. It consumes *where packages
land*, not requirements.txt, so 13a's inventory missed it. Satisfy it by putting the venv's
bin on PATH in the image rather than rewriting start.sh — fewer files move, and start.sh
stays runnable outside Docker.

**Watch** `.dockerignore`'s `**/.venv` and `**/venv` rules stay after this leg. What 13b
clears is the comment above them, not the rules: `COPY backend/ .` would otherwise copy a host
venv into the image — a macOS venv into a Linux image, or a second one over the image's own.
The `--probe` done-when above is the net that catches it.

### 13c — remove the scaffolding, take the upgrade (version upgrade) --- planned

**Kind:** upgrade

**Decide before commit 1: which Python.** You develop on 3.13.7 and ship on 3.12 (`Dockerfile`,
`requires-python = ">=3.12"`). Re-locking on an interpreter prod does not run means reading the
upgrade diff in an environment nobody deploys. Two ways out, and this leg needs one of them:
- pin dev down to 3.12 (a `.python-version` in `backend/`). No Dockerfile change, this leg
  stays single-factor, and it is the cheaper default.
- or bump the image to 3.13. That is a real upgrade of its own and a second factor inside a leg
  that already moves every version — if you want it, it is its own leg, not a line here.
The older note to re-lock with `--python 3.13.7` only holds if the image moves too. (Was H-6,
and the [SPRINT-13-CLEANUP] interpreter note in Housekeeping.)

**Done when**
- [ ] constraint-dependencies is gone from pyproject and `uv lock --check` is clean
- [ ] the uv.lock diff has been read, not skimmed — that diff IS the upgrade
- [ ] `dep_freeze.py compare` re-run against the same baseline and its output read. It is
      expected to differ now; that difference is the upgrade stated in package terms
- [ ] test counts: 106 collected − 29 from `test_dep_freeze.py` = 77 collected, with the same
      18 failures in test_tailoring.py (13a baseline: 106 collected, 88 passed, 18 failed)
- [ ] docker build + run smoke passes
- [ ] `docs/DEVLOG/sprints/sprint13/` deleted — after `compare`, the freeze artifacts have no
      consumer left (was H-5)

**Commits**
| # | | |
|---|---|---|
| 1 | remove scaffolding | delete constraint-dependencies, re-lock with upgrades allowed |
| 2 | absorb breakage | whatever the bumps broke — may be zero commits, may be several |
| 3 | delete the scaffolding | `backend/scripts/dep_freeze.py` and `backend/tests/test_dep_freeze.py`, once the compare above has been read. Both docstrings already say they die here. |

**Watch** sqlmodel is pre-1.0, so any bump is potentially breaking; pydantic, SQLAlchemy and
the anthropic SDK all move fast. If this blows the appetite, cut scope not time: upgrade a
named subset and leave the rest locked.

### 13d — dependency hygiene (refactor) --- planned

**Kind:** refactor — the suite is the invariant.

The two second-factor items 13a tagged and deferred. Both are declaration-only, both move the
lock, and that is why they wait until 13c has read its upgrade diff.

**Done when**
- [ ] `python-multipart` is gone from pyproject and the suite is unchanged — zero
      UploadFile/Form/File usage anywhere in app/, confirmed in 13a
- [ ] `sqlalchemy[asyncio]` is declared, so nothing relies on greenlet arriving transitively
- [ ] `uv lock --check` clean, docker build + run smoke passes
- [ ] no `[SPRINT-13-CLEANUP]` markers are left in the repo

**Commits**
| # | | |
|---|---|---|
| 1 | drop a root | remove python-multipart, re-lock |
| 2 | declare a root | `sqlalchemy[asyncio]`, re-lock |

(Was H-2 and H-3, which had no real when.)

### After Sprint 13 closes

Two items that have nothing to do with dependencies but need a when, parked here so they land
as soon as the sprint is off the critical path.

- [ ] Redact the recipient block in `docs/feedback/asks/2026-03-15-beta-invite.md` — seven
      names and email addresses, one of them a work address, public since `936ed83`. The front
      matter already records "7", so the file loses nothing. Redacting the file does not remove
      it from the public log, so decide separately whether that history gets rewritten.
- [ ] Recover `test-vehicles/schema-extraction/ledger.py` and narrow the rule that swallowed
      it. That lab's `.gitignore` has `ledger*.*`, which matches the module as well as its data
      files, so the module was never committed and is not in this clone. `lab.py` imports it at
      module level, so the lab cannot start — `--dry-run` included. It should still exist on
      the Windows machine.

### Out of Scope (13)
- No CI exists. `uv lock --check` is a one-line pre-deploy gate once there's somewhere to run
  it → Sprint 15 (Developer tooling), see T-1


---


## Sprint 14 — Tests --- planned

**Legs:** fix the red suite (bugfix), then fill the gaps (feature).

Fill concrete gaps. The goal is confidence before auth (Sprint 16), and before CI, which can't
live on a red suite.

**First: the 18 failures.** `tests/test_tailoring.py` has 18 failing tests with one cause,
session/DB wiring. They predate Sprint 13 and were not fixable inside it — the 13a baseline
recorded the same 18 before and after the migration. Until they are green, every "test counts
unchanged" done-when in this doc is measuring a suite that is already red. (Was a
[SPRINT-13-CLEANUP] item in Housekeeping, which named the wrong sprint.)

Backend — new files:
- `test_analysis.py`: batching logic (5-JD boundary, partial final batch), SSE event generation (`batch_start`, `jd_result`, `batch_complete`, `analysis_complete`), error/retry with mocked Claude client, meta-analysis accumulation across batches. This is the biggest gap — the core analysis flow has zero dedicated tests.
- `test_jds.py`: zip package download (ADR-014), docx download, JD CRUD (PATCH fields, status override), single-JD tailoring kickoff. Currently only tested indirectly through session-level tests.

Backend — extend existing:
- `test_tailoring.py`: verify the 6 `failed` status paths added in Sprint 11 (missing template, missing JD, missing resumes, Claude API error, JSON parse error, docx generation error). These are the error paths that used to silently bail.

Frontend — extend existing:
- `TailoringPage.test.jsx`: polling lifecycle test (advance fake timers, assert queued→processing→ready transition updates UI). Highest-complexity React test pattern — fake timers + async state + `act()` wrapping. Currently 12 tests cover rendering and button clicks but not the polling state machine.

Frontend — audit:
- Ownership/auth guard tests: verify that session-scoped pages handle "session not found" and "session belongs to different user" (setup for Sprint 16). This is the "multi-user safety" item — make it concrete now even though auth is a stub.

Context load: `test_analysis.py` is the heavy one — analysis.py is 330 lines, the SSE protocol has 4 event types, and the mocked Claude client needs to return structured JSON in batches. The rest are incremental additions to existing test files. Fits one context window.


## Sprint 15 — Developer tooling --- planned

**Kind:** feature — build the pipeline that isn't there.

Payoff is real but shouldn't block auth: it buys back the hour uv's directory-bound
environment costs, makes the context check something that actually runs, and gives
`uv lock --check` and `--probe` a home. `673f7a0` would have been caught here rather than by
Railway.

- Makefile wrapping the uv commands, with a preflight target — see the Makefile item in Tech Debt
- Wire in `scripts/check_docker_context.py --probe` and `uv lock --check`
- A first CI job, once the suite is green (Sprint 14)

Candidate scope when this gets planned: the levels in the Housekeeping overlap-check item, and
T-1, T-3 and T-4 in Tech Debt. Skip the git-hook level — a Makefile plus CI covers it, and
`--no-verify` makes a hook optional anyway.


## Sprint 16 — Auth, magic link accounts --- planned

Cookie auth shipped in Sprint 12. Anonymous sessions work, data is isolated per browser, beta testers are unblocked.

What's left for real accounts:
1. Magic link flow: email + token, no passwords. Needs an email provider (Resend or SES), a token table, expiry logic.
2. Account conversion: anonymous User row adopts into a permanent account when user enters email. Data carries over — no migration, just set `user.email` and clear the expiry.
3. Frontend: login page, protected routes, auth state management.

**Decide here: anonymous retention.** The cookie is 30 days today (`sessions.py`, "30 days for
beta") and `auth_token_expires_at` is never set, while the data model documents 7 days for
anonymous users. 30 is right while I am the anonymous user; 7 is the intent once there is a
login to convert into. One of the two has to change when accounts land.

Cookie auth covers beta. This becomes relevant when persistence beyond 30 days matters or when users want to switch devices.


## Sprint 17 — Billing --- planned

Not planned in detail here yet; the notes live outside the repo. This entry exists so the
number is real and Phase 1's scope is visible in one place.

Prerequisite already named in the Phase 1 overview: per-user cost caps and metering. My API key
pays for every beta session today.

---

## Deferred from Phase 0

**Prompts — IP and extraction** (ADR-013). Pull the prompts out of the repo. This is about IP
protection before the repo gets public attention, not about functionality, and the placeholder
`backend/app/prompts/` in the README tree is where the files were meant to go. Checked
2026-09-16:
- The two system prompts are string constants: `ANALYSIS_SYSTEM_PROMPT` in `services/analysis.py` (committed 2026-03-04) and `TAILORING_SYSTEM_PROMPT` in `services/tailoring.py` (committed 2026-03-05). `services/claude.py` only mentions one in a docstring. The repo is public, so both are also in its public history; extracting them now hides future edits, not these versions.
- Also public: `docs/original-prompts.md`, and the seeded PromptTemplate defaults in `backend/scripts/seed.py` (public by design, per ADR-013).
- The backup setup was never used. `sync-prompts.sh` copies a root `prompts/` folder into a sibling clone at `../application-pipeline-prompts`, and neither folder exists. The private repo `sooperD00/application-pipeline-prompts` holds only a `.gitkeep` (three "prompt update" commits, all from 2026-03-01).
- Open question: where the files live. The README tree says `backend/app/prompts/`, but `sync-prompts.sh` expects a root `prompts/`. Either way, `.gitignore` and `.dockerignore` both exclude `prompts` at any depth, so the files reach neither GitHub nor a Docker build.
- Open question: how they reach production. Railway builds from the GitHub snapshot, where git-ignored files never exist, so "loaded at startup" needs another way in (ADR-013 lists env vars and a private submodule).
- The in-code TODO in `analysis.py` ("move this to PromptTemplate table") points the other way: it would move the analysis system prompt into the user-editable table instead of into a file.

**Activities** (`routers/activities.py`, `services/activities.py`): The data model is in place (Activity table, ActivityType enum, cascade templates designed in service-layer-notes.md), but no router, service, or frontend exists. The README tree and architecture.md list these as Phase 0 scope, but they aren't needed for the core flow (paste → analyze → tailor → download). Deferring to Phase 1 when the Full Tracker makes them visible and useful.

**Resume input for analysis and tailoring.** Every resume the user has, up to 3, is sent as text in the prompt: `_format_resumes()` in tailoring.py and `_resume_block()` in analysis.py each concatenate all of them. Nothing selects one — not for content, not for formatting. The model reads whatever text sits in the resume fields and decides what to draw on per JD, which is the intended behaviour and stays the default. Blending across versions is something a human can't do at all.

`resume_id` on TailoringJob is not a record of a choice: `resumes[0].id` is stored to satisfy the FK. Read it as "one of the resumes that went in", not "the resume used".

Phase 1+ adds an optional override: per-JD resume picker in the Tab 4 kickoff modal where the user can select a single resume or a subset instead of sending all three. Backend changes: add an optional `resume_ids` body param to the analyze and batch-tailor endpoints, filter the resume query when present, fall back to "all resumes" when absent. Frontend: resume chip selector in the tailoring kickoff UI, default state = "All". That is also what would finally make `resume_id` mean something — the user constrains the input set, so the FK records a decision someone actually made.

(Note: `analyzeSession()`, `batchTailor()`, and `createTailoringJob()` in client.js were scaffolded with a `resume_id` parameter anticipating this feature. The backend endpoints never accepted it — they fetch all resumes internally. The phantom params were cleaned up in Sprint 10 (`analyzeSession`) and Sprint 11 (`batchTailor`, `createTailoringJob`) respectively. When resume selection is implemented, the parameter comes back with real plumbing behind it.)

**Resume snapshot architecture** see ADR-017
session_resume_snapshots table, session locking, clone session. Phase 1+.
ADR, a new table, migrations, service changes, and frontend work - a full context window (large sprint).

---

## Housekeeping (any sprint)

- [ ] [SPRINT-15-CLEANUP]: .gitignore/.dockerignore overlap check. The first attempt (673f7a0)
      broke the Railway deploy and was reverted (fe8794e). It's parked in
      `test-vehicles/dockerignore-check/`, whose README has the details. (That README is frozen
      at what it knew on 2026-09-16 and calls this Sprint 14 — read it as Sprint 15.)
      `scripts/check_docker_context.py` is on main (see the Sprint 13a close-out).
      How far to take it, lightest first:
      Level 0, documented command: done (README Quick Start → Checks)
      Level 1, task runner: see the Makefile item in Tech Debt
      Level 2, git hook: either the pre-commit framework (1 file + `pre-commit install` on
         each machine) or `.githooks/` + `git config core.hooksPath .githooks`. Run it only on
         commits that touch an ignore file or the Dockerfile. Needs Docker running, and
         `--no-verify` skips it. ~20–30 min. The same hook file can run a Python linter later.
         Probably skip it: Level 1 plus Level 3 covers the same ground.
      Level 3, CI: see T-1
      Level 4, tests for the script: see T-3
- [ ] Surface the model in the app, and make it changeable without editing code. Today it is
      `default_model` in config.py, overridable by the `DEFAULT_MODEL` env var (README →
      Choosing the Model). `model_used` is already stored per tailoring job, so the data exists
      and nothing displays it. Candidate scope for the Phase 1 app/dev metrics work, where cost
      per model belongs anyway. Whether the *user* picks is a later decision.
- [ ] `datetime.utcnow()` deprecation warnings — switch to `datetime.now(datetime.UTC)` across models.py (7 occurrences), tailoring.py (1), and jds.py (1, in the zip's notes.txt header)
- [ ] `HTTP_422_UNPROCESSABLE_ENTITY` deprecation — FastAPI renamed to `HTTP_422_UNPROCESSABLE_CONTENT`. 11 occurrences across jds.py (2), resumes.py (4), sessions.py (5).
- [ ] Timestamps showing 1 day ahead in Oregon (UTC storage, no timezone conversion). Tolerable while I'm the only one reading them, but the beta testers already see this.
- [ ] assets/react.svg and public/vite.svg still in tree — harmless, clean up whenever
- [ ] api/client.js has no retry logic or token refresh — Phase 1 (auth)
- [ ] Tailwind @theme uses Inter/JetBrains Mono but doesn't load them from Google Fonts — add <link> to index.html when you care about typography (or never if system fonts are fine)
- [ ] add press enter to submit form on SessionsPage.jsx (a simple wrap that Claude can do)
- [ ] ability to Edit/Delete JD cards in sessions/:id (use same implementation as for edit/delete resume cards)
- [ ] Card grid sort: after analysis starts, sort by [status_priority, number] instead of just number. Apply cards float to top after each batch_complete, giving the user real-time feedback on which JDs survived. Toggle: sort by number when status=active (paste order matters during data entry), sort by status when analyzing/complete. Small change in SessionDetailPage's mergedJds sort comparator.
- [ ] make the JD cards have an aspect ratio like an actual playing card (right now it's longer horizontally); then, make them in a ribbon spread instead of currently they don't overalp at all. Use ~generous and equal spacing at first (before analysis) so user can see beginning of title/subtitle. But then after analysis, make the "Apply" cards trickled to the left not overlapping, then ribbon spread the "maybe" results in the middle with medium overlap, and ribon spred the "no" results with very tight spacing / high overlap on the right.
- [ ] No AbortController on SSE or polling fetches. `analyzeSession()` has no AbortController — useSSE.abort() cancels the reader but doesn't abort the fetch, so the backend generator keeps running. Same pattern on TailoringPage polling. Harmless for single-user MVP (results still write to DB), but wasteful. Phase 1.
- [ ] MetaAnalysis text is rendered as whitespace-pre-wrap plain text. If Claude's meta_analysis includes markdown formatting (bold, lists), it won't render. Could add a lightweight markdown renderer later, but plain text is fine for MVP — the analysis prompt doesn't ask for markdown.
- [ ] The Analyze button always says "Analyze" even for re-analysis. Could say "Re-analyze" when session.status === 'complete'. Polish, not function.
- [ ] Add a meta analysis to tailored resumes, either "all" or maybe that's too much... at least in 1 session... to see if it was even worth it to tailor. This gives me (the dev) feedback on how worthwhile this part of the tool is, and gives the user feedback that this was actually worth the money, rather than just having claude pick "apply to these 6 out of 25 and use resume #1" from the "analyze" phase on its own. This could just be sending the completed tailored resumes and JDs through a fresh claude call and asking for this analysis and displying in a box.
- [ ] Tab 4 "Batch Tailor All" button could also live on Tab 1 (next to Analyze) — Nicole will decide placement later
- [ ] Jobs where the JD status changed AFTER tailoring (apply → maybe) still show on Tab 4. This is intentional (output exists), but could add a visual indicator "JD status changed to maybe" in a future sprint.
- [ ] Polling has no exponential backoff — 3s forever until terminal. Fine for MVP, but if someone leaves the tab open overnight it's chatty. Phase 1: increase interval after 60s.
- [ ] JDPasteForm.jsx: auto-populate company/role from first lines of pasted text (in-code TODO line 71). Also: make company/role extraction a user-toggleable preference (line 52). Phase 1 polish.
- [ ] NotFoundPage.jsx: update 404 copy once `/tracking` becomes the index route (ADR-016 scope, Phase 1+). In-code TODO line 15.
- [ ] Sprint 11 migration (`6bc0f4c28a4a`) added `failed` to the TailoringStatus enum but doesn't retroactively fix stale rows. If you have old jobs stuck at `queued` from before Sprint 11, they'll stay there. Manual SQL or just delete them.
- [ ] add a "download all" button (downloads zip with folder structure like session_title_timestamp/[company_role_timestamp_folders]/[files] so user can just get them all if they've iterated a process that they don't usually have to chat with claude to revise and can just open and check by themselves before doing the apply
- [ ] onRetry cap for createTailoringJob (FE and BE). no runaway loop to worry about here but, need to make a cap to limit my cost (hitting my claude API key) for 1) friends testing and 2) probably my first real paying users will just have a limit for a set dollar subscription or batch package 3) I can add like... a-la-carte pricing later if I want.). `tailoring.py` update for later (unless we think my friends are gonna hit this 400 times...).
- [ ] TailoringPage: extract useTailoringData hook (polling, fetchJobs, derivations) when Phase N inline chat adds enough complexity that the page's render body obscures the JSX. Currently ~15 lines of derivation logic — comfortable, but one more feature tips it.
- [ ] The "failed" error paths in tailoring.py are repetitive (6x the same pattern: set status, add, commit, return). A context manager or decorator could DRY this up. Not worth the abstraction for 6 lines each, but note it if it grows.
- [x] H-4 .dockerignore does not exclude backend/venv/ (the OLD venv) either. Whether it is
      currently entering the build context depends on the Dockerfile's COPY lines, which I
      did not read. Worth checking in 13b, where "image size is same or smaller" is already
      a done-when — if the old venv has been shipping, that is where the size went. H-1
      makes it moot. [13b]
      Resolved 2026-09-16 in 13a commit 3 (da59650): `.dockerignore` excludes `**/venv` and
      `**/.venv`. Before that, `COPY backend/ .` copied a local backend/venv into local builds
      (Railway never had one, since it's gitignored). For 13b's image-size check, compare
      against a build from da59650 or later.

## Tech Debt (deferred, maybe long term)
- [ ] Phase 1+: extract repeated Tailwind class strings into shared component styles.
- [ ] Phase 1+: extract shared test factories and mocks once data models stabilize, especially if same factory/mock appears in 3+ test files and the shape is identical. `__tests__/factories.js` and `__tests__/mocks.js`
- [ ] tooltip "Select or create a session to unlock this step" appears after 1s delay = browser-native `title` attribute behavior (delay hardcoded in the browser, not my app). Add a custom tooltip component to make it ~instant (polish)
- [ ] Phase 1: SessionLayout fetch has no retry/error-retry UX — user must manually navigate away and back on transient errors. Fine for single-user MVP; Phase 1 adds retry button.
- [ ] Phase 1: The session picker is the /sessions list page (click a row to enter). A nav dropdown picker was mentioned in sprint spec — deferred; the list page approach is simpler and sufficient. If dropdown is wanted later, it reads from the same listSessions() endpoint.
- [ ] Phase 1: No loading skeleton / optimistic UI on addJD — the card grid waits for refreshSession() to resolve. Acceptable latency for local dev; may want optimistic insert for prod. Phase 1.
- [ ] Phase 1: No "unsaved changes" guard on the form — if you click Edit while mid-create, the form overwrites silently. Acceptable for single-user MVP; revisit in Phase 1 multi-user.
- [ ] Phase N. line-clamp-3 depends on -webkit-line-clamp which is non-standard but supported in all modern browsers. If it ever breaks, fall back to a JS truncation.
- [ ] Phase N: observe behavior post-launch. The Analyze button re-enables immediately on error via `finally { setIsAnalyzing(false) }`. No retry budget or rate limiting exists yet. Monitor real usage for repeated error-retry loops before deciding whether to add a retry counter, cooldown timer, or backend cost cap. Backend concern to gate at the API/billing layer? or also on the button? Precedent: Sprint 3 batch analysis already has per-session cost tracking that could be extended. Status: Acceptable risk for MVP. Revisit after first real-user sessions.
- [ ] Phase N: The jdOverrides state overlay pattern works but creates a brief window where context jds and overrides can disagree (between stream end and refreshSession resolving). This is harmless — the override data matches what the backend wrote — but a more robust pattern would be to optimistically update the context itself. Phase 1 if it causes issues.
- [ ] Phase N: On "only apply jobs in Tab 4"- a nuance. The batch-tailor endpoint only creates jobs for apply-status JDs (backend enforced). The listSessionTailoringJobs endpoint returns all tailoring jobs that exist for the session — so if a JD was "apply" when tailored but later changed to "maybe," its job still shows up. I'll show whatever the backend returns rather than client-side filtering, since the output exists and is useful regardless of current status. The per-JD "Tailor" button on each card will only be active for apply-status JDs without an existing job. gotta figure out exactly how we want to deal with this in Phase N when we let users change "apply" status to "maybe" or whatever.
- [ ] Phase N: currently no place to see the claude analysis for each JD (usually he returns a nice chart of skill matches and summary)
- [ ] [SPRINT-15-CLEANUP] Makefile wrapping the uv commands — uv binds to an
      environment based on the working directory and says nothing about it (cost an
      hour in 13a when a stale root .venv answered instead of backend/.venv; the hand
      guards are in 13b's prework). A recipe that cd's first removes the failure mode
      instead of detecting it.
      Targets: preflight (print sys.prefix, fail unless it ends in backend/.venv), sync,
      test, test-frontend, lock-check (uv lock --check + uv sync --check), seed, run.
      Every uv target depends on preflight.
      Also check-context (`python3 scripts/check_docker_context.py --probe`), and any
      docker-build target runs it first. (L1 of the overlap check, see Housekeeping.)
      Do NOT carry over the 13a/13c scaffolding targets (dep_freeze compare, uv export) —
      they die with their legs.
      Gate: after 13c (open) AND after the mac move (closed 2026-09-16). make is not in
      Git Bash; it arrives with the Xcode CLT, which is what makes this worth doing at all.
      Watch: macOS ships GNU make 3.81 (2006 — Apple stopped at the GPLv3 line), so
      `.ONESHELL:` silently does nothing. Each recipe line gets its own shell, so
      `cd backend` on one line does not persist to the next. Write
      `cd backend && uv sync` on one line, or brew a newer make (lands as `gmake` under
      /opt/homebrew unless you add the gnubin path). Getting this wrong reproduces the
      exact bug the Makefile exists to prevent.
      Success condition: it REPLACES typing uv directly. A wrapper used half the time is
      a second way to be in the wrong directory, not a fix.   [techdebt, Sprint 15]
- [ ] T-1 `uv lock --check` as a pre-deploy gate — one line, no CI to put it in. Already in
      the doc's Out of Scope. When CI exists, run `python3 scripts/check_docker_context.py
      --probe` in the same job. That's L3 of the overlap check: the only layer you can't skip,
      and `--probe` needs no real ignored files, so it works in CI. Try the workflow on a
      branch first (673f7a0's workflow failed on every push to main). ~45 min. [Phase N]
- [ ] T-3 tests for `scripts/check_docker_context.py` (L4 of the overlap check), only if the
      script grows or others rely on it. Unit tests for the pure functions (probe paths,
      glob → file name, Dockerfile COPY parsing), plus one Docker test that skips when Docker
      is off. 1–2 files, ~1–2 h. [Phase N]
- [ ] T-4 `--diff` mode for the same script. The check catches shipping files git ignores,
      not excluding files the app needs. Compare the build context before and after a
      `.dockerignore` edit (done by hand for ea7213e). Until then, a docker build plus a smoke
      test covers that direction. [Phase N]
