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
- Railway database backups
- Suite health, and whatever tooling this phase warrants for quality and maintainability

**Sprints**

- 13 — Backend dependencies, pip → uv — in progress (13a done, 13b/13c/13d planned)
- 14 — Tests — planned
- 15 — Code hygiene — planned
- 16 — Developer tooling — planned
- 17 — Auth, magic link accounts — planned
- 18 — Billing, and the cost caps it depends on — planned
- Frontend polish — parked, deliberately last and deliberately unnumbered

Numbers are expectations, not commitments: they can be bumped, split or dropped. The one rule
is that whatever a `[SPRINT-<N>-CLEANUP]` marker names has to exist in this list — which is why
the parked sprint has no number until something needs to point at it.

---

## Sprint 13 — Backend dependencies --- in progress

Migrate backend dependency management from pip to uv.
**Kind:** migration
**Legs:** migration, consumer flip, version upgrade — the first two move packaging (factor 1) with versions pinned; the third moves versions (factor 2) with packaging fixed. Merging the last two means a red suite can't say which.

**Why now** CE! (Copy Exactly!, the Intel sense — match the current SWE standard rather than
invent a local one). Also: requirements.txt is a pip freeze —
41 pinned lines, hand-appended since, in which the 15 packages this app actually asks for (11
runtime, 4 test-only) are indistinguishable from the 26 that came along for the ride. Nothing
declares what this project actually requires, so nothing can be upgraded deliberately.
(Planning guessed 13 roots in 20 transitives; counted at 13a close, it was 15 in 41.)

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
      13b nor 13c consumes the old venv. (Pulled from Housekeeping, 2026-09-17.)
- [x] `.gitattributes` with `* text=auto eol=lf`, plus `git add --renormalize .` — done
      2026-09-17, in its own commit so it reverts cleanly. 29 tracked files were CRLF in the
      index against 87 LF, with no `.gitattributes` at all; 27 normalized, and every blob was
      compared with CRs stripped to prove nothing but line endings moved.
      `test-vehicles/dockerignore-check/` is exempt via `-text`: two of its files are
      byte-for-byte copies of 673f7a0, and its README records their CRLF endings as one of the
      findings, so normalizing them would have deleted the evidence they were parked to show.
      Two side effects worth knowing. `start.sh` can now never be committed with CRLF, which
      would break the container's shebang — that trap is closed by construction rather than by
      luck. And `dep_freeze.py`'s CRLF-preserving read and write helpers are vestigial as of
      this commit; harmless, and they die with the script in 13c.
      (Pulled from Tech Debt, 2026-09-17, where it was filed as a requirements.txt symptom
      rather than the repo-wide split it turned out to be.)

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
- This Mac has neither venv yet, being a fresh clone. Sprint 16's Makefile is the planned
  guard (a preflight target that fails unless `sys.prefix` ends in `backend/.venv`).

**Done when**
- [ ] `docker build` succeeds installing from pyproject + uv.lock, with no requirements.txt in the repo
- [ ] the built image runs migrations and starts uvicorn
- [ ] image size is same or smaller — compare against a build from `da59650` or later, never
      anything earlier. Until that commit `.dockerignore` excluded neither `**/venv` nor
      `**/.venv`, so `COPY backend/ .` copied a local backend/venv into local builds and
      whatever size that added is not prod's baseline. Railway never had one, being gitignored
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
The older note to re-lock with `--python 3.13.7` only holds if the image moves too. (Pulled
from Housekeeping, 2026-09-17, where the skew and the note sat as two separate items.)

**Done when**
- [ ] constraint-dependencies is gone from pyproject and `uv lock --check` is clean
- [ ] the uv.lock diff has been read, not skimmed — that diff IS the upgrade
- [ ] `dep_freeze.py compare` re-run against the same baseline and its output read. It is
      expected to differ now; that difference is the upgrade stated in package terms
- [ ] test counts: 106 collected − 29 from `test_dep_freeze.py` = 77 collected, with the same
      18 failures in test_tailoring.py (13a baseline: 106 collected, 88 passed, 18 failed)
- [ ] docker build + run smoke passes
- [ ] `docs/DEVLOG/sprints/sprint13/` deleted — after `compare`, the freeze artifacts have no
      consumer left (pulled from Housekeeping, 2026-09-17)

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

(Pulled from Housekeeping, 2026-09-17, where both sat with no real when.)

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
  it → Sprint 16 (Developer tooling), which owns the first CI job


---


## Sprint 14 — Tests --- planned

**Legs:** fix the red suite (bugfix), then fill the gaps (feature).

Fill concrete gaps. The goal is confidence before auth (Sprint 17), and before CI, which can't
live on a red suite.

**First: the 18 failures.** `tests/test_tailoring.py` has 18 failing tests with one cause,
session/DB wiring. They predate Sprint 13 and were not fixable inside it — the 13a baseline
recorded the same 18 before and after the migration. Until they are green, every "test counts
unchanged" done-when in this doc is measuring a suite that is already red. (Pulled out of
Housekeeping, where it was marked for Sprint 13 — the wrong sprint.)

Backend — new files:
- `test_analysis.py`: batching logic (5-JD boundary, partial final batch), SSE event generation (`batch_start`, `jd_result`, `batch_complete`, `analysis_complete`), error/retry with mocked Claude client, meta-analysis accumulation across batches. This is the biggest gap — the core analysis flow has zero dedicated tests.
- `test_jds.py`: zip package download (ADR-014), docx download, JD CRUD (PATCH fields, status override), single-JD tailoring kickoff. Currently only tested indirectly through session-level tests.

Backend — extend existing:
- `test_tailoring.py`: verify the 6 `failed` status paths added in Sprint 11 (missing template, missing JD, missing resumes, Claude API error, JSON parse error, docx generation error). These are the error paths that used to silently bail.

Frontend — extend existing:
- `TailoringPage.test.jsx`: polling lifecycle test (advance fake timers, assert queued→processing→ready transition updates UI). Highest-complexity React test pattern — fake timers + async state + `act()` wrapping. Currently 12 tests cover rendering and button clicks but not the polling state machine.

Frontend — audit:
- Ownership/auth guard tests: verify that session-scoped pages handle "session not found" and "session belongs to different user" (setup for Sprint 17). This is the "multi-user safety" item — make it concrete now even though auth is a stub.

**Also in scope**
- [ ] Extract shared test factories and mocks — `__tests__/factories.js` and `__tests__/mocks.js`
      — but only if the same factory or mock has turned up in 3+ test files with an identical
      shape by the time you are in there. Data models have to stabilize first, and this sprint
      is when you find out whether they have.

Context load: `test_analysis.py` is the heavy one — analysis.py is 330 lines, the SSE protocol has 4 event types, and the mocked Claude client needs to return structured JSON in batches. The rest are incremental additions to existing test files. Fits one context window.


## Sprint 15 — Code hygiene --- planned

**Kind:** refactor — the suite is the invariant.

Deprecations, dead files and small corrections, cleared before the next feature lands on top of
them. Nothing here changes behaviour a user would notice, except the timestamps, which are
wrong today.

**Scope**
- [ ] `datetime.utcnow()` deprecation warnings — switch to `datetime.now(datetime.UTC)` across
      models.py (7 occurrences), tailoring.py (1), and jds.py (1, in the zip's notes.txt header)
- [ ] `HTTP_422_UNPROCESSABLE_ENTITY` deprecation — FastAPI renamed it to
      `HTTP_422_UNPROCESSABLE_CONTENT`. 11 occurrences: jds.py (2), resumes.py (4), sessions.py (5)
- [ ] Timestamps read a day ahead in Oregon — stored UTC, displayed with no timezone
      conversion. Tolerable while I was the only reader; the beta testers already see it
- [ ] Delete `assets/react.svg` and `public/vite.svg` — leftover Vite scaffolding, unreferenced
- [ ] Press Enter to submit the create-session form on SessionsPage.jsx — a simple wrap
- [ ] Clear the tailoring jobs stuck at `queued` from before the `failed` status existed. The
      Sprint 11 migration (`6bc0f4c28a4a`) added `failed` to the TailoringStatus enum but does
      not backfill, so anything queued before it sits there forever. Manual SQL, or delete them
- [ ] Delete `sync-prompts.sh`, or point it at something that exists. It copies a root
      `prompts/` folder into a sibling clone at `../application-pipeline-prompts`; neither
      folder exists on disk, and the private repo `sooperD00/application-pipeline-prompts` holds
      nothing but a `.gitkeep` from three "prompt update" commits on 2026-03-01. The backup it
      implies has never run once. Read the prompt-extraction item in Tech Debt first: if
      extraction picks a different mechanism, this script is the wrong shape anyway and deleting
      it is the honest move


## Sprint 16 — Developer tooling --- planned

**Kind:** feature — build the pipeline that isn't there.

Payoff is real but shouldn't block auth: it buys back the hour uv's directory-bound environment
costs, makes the context check something that actually runs, and gives `uv lock --check` and
`--probe` a home. `673f7a0` would have been caught here rather than by Railway.

**Scope**
- [ ] Makefile wrapping the uv commands, with a preflight target. uv binds to an environment
      based on the working directory and says nothing about it — that cost an hour in 13a, when
      a stale root `.venv` answered instead of `backend/.venv`, and 13b's prework is the
      by-hand version of this guard. A recipe that cd's first removes the failure mode instead
      of detecting it.
      Targets: preflight (print sys.prefix, fail unless it ends in backend/.venv), sync, test,
      test-frontend, lock-check (`uv lock --check` + `uv sync --check`), seed, run. Every uv
      target depends on preflight. Also check-context (`python3
      scripts/check_docker_context.py --probe`), and any docker-build target runs it first.
      Do NOT carry over the 13a/13c scaffolding targets (dep_freeze compare, uv export) — they
      die with their legs.
      Gate: after 13c. The mac move closed 2026-09-16, and that is half of why this is worth
      doing: make is not in Git Bash, it arrives with the Xcode CLT.
      Watch: macOS ships GNU make 3.81 (2006 — Apple stopped at the GPLv3 line), so
      `.ONESHELL:` silently does nothing. Each recipe line gets its own shell, so `cd backend`
      on one line does not persist to the next. Write `cd backend && uv sync` on one line, or
      brew a newer make (lands as `gmake` under /opt/homebrew unless you add the gnubin path).
      Getting this wrong reproduces the exact bug the Makefile exists to prevent.
      Success condition: it REPLACES typing uv directly. A wrapper used half the time is a
      second way to be in the wrong directory, not a fix
- [ ] A first CI job, once the suite is green (Sprint 14). `uv lock --check` is a one-line
      pre-deploy gate with nowhere to run it today; put `python3 scripts/check_docker_context.py
      --probe` in the same job, since `--probe` needs no real ignored files and so works in a
      fresh clone. Try the workflow on a branch first — 673f7a0's workflow failed on every push
      to main. ~45 min
- [ ] Decide how far to take the .gitignore/.dockerignore overlap check. The first attempt
      (673f7a0) broke the Railway deploy and was reverted (fe8794e); it is parked in
      `test-vehicles/dockerignore-check/`, whose README has the details. (That README is frozen
      at what it knew on 2026-09-16 and calls this Sprint 14 — read it as this sprint.)
      `scripts/check_docker_context.py` is already on main. Lightest first:
      Level 0, documented command: done (README Quick Start → Checks)
      Level 1, task runner: the Makefile item above
      Level 2, git hook: either the pre-commit framework (1 file + `pre-commit install` on each
         machine) or `.githooks/` + `git config core.hooksPath .githooks`. Run it only on commits
         that touch an ignore file or the Dockerfile. Needs Docker running, and `--no-verify`
         skips it. ~20–30 min. The same hook file can run a Python linter later.
         Probably skip it: Level 1 plus Level 3 cover the same ground
      Level 3, CI: the CI item above
      Level 4, tests for the script: in Tech Debt, worth it only if the script grows


## Sprint 17 — Auth, magic link accounts --- planned

Cookie auth shipped in Sprint 12. Anonymous sessions work, data is isolated per browser, beta testers are unblocked.

What's left for real accounts:
1. Magic link flow: email + token, no passwords. Needs an email provider (Resend or SES), a token table, expiry logic.
2. Account conversion: anonymous User row adopts into a permanent account when user enters email. Data carries over — no migration, just set `user.email` and clear the expiry.
3. Frontend: login page, protected routes, auth state management.

**Decide here: anonymous retention.** The cookie is 30 days today (`sessions.py`, "30 days for
beta") and `auth_token_expires_at` is never set, while the data model documents 7 days for
anonymous users. 30 is right while I am the anonymous user; 7 is the intent once there is a
login to convert into. One of the two has to change when accounts land.

**Also in scope**
- [ ] `api/client.js` has no retry logic and no token refresh. Both belong with real accounts:
      a token that can expire needs a refresh path, and a fetch wrapper that never retries turns
      every transient blip into a failure the user has to interpret

Cookie auth covers beta. This becomes relevant when persistence beyond 30 days matters or when users want to switch devices.


## Sprint 18 — Billing --- planned

Not planned in detail here yet; the notes live outside the repo. This entry exists so the number
is real and Phase 1's scope is visible in one place.

Prerequisite already named in the Phase 1 overview: per-user cost caps and metering. My API key
pays for every beta session today, so the limits work that has been piling up belongs here with
it.

**Scope — cost and limits**
- [ ] Cap retries on `createTailoringJob`, front end and back. There is no runaway loop to worry
      about; the cap is what limits my spend against my own API key. Friends testing now, and
      later a set dollar subscription or batch package per paying user, with à-la-carte pricing
      as an option. `tailoring.py` is where the backend half lands
- [ ] Give polling exponential backoff. It is 3s forever until terminal today, which is chatty
      if someone leaves the tab open overnight — increase the interval after 60s
- [ ] Add AbortController to the SSE and polling fetches. `analyzeSession()` has none, so
      `useSSE.abort()` cancels the reader but not the fetch and the backend generator keeps
      running; TailoringPage polling has the same pattern. Harmless for a single user, since the
      results still write to the DB, but it is paid-for work nobody is waiting on
- [ ] Decide where the retry budget lives, once there is real usage to look at. The Analyze
      button re-enables immediately on error via `finally { setIsAnalyzing(false) }`, with no
      retry counter, cooldown, or backend cap. Gate it at the API/billing layer, on the button,
      or both. Per-session cost tracking from Sprint 3 is the precedent to extend. Acceptable
      risk for MVP; revisit after the first real-user sessions


## Frontend polish — parked, last in Phase 1

**Kind:** decide when it gets planned. A grab-bag has no single ordering heuristic, and choosing
one now would be pretending.

No number until it is scheduled. A number is a promise of order and this one is deliberately
last; it takes the next free number the day something in source needs to point at it.

Quarantined UI and product judgment: ideas I am not ready to finalize, kept here so they are not
lost and do not leak into sprints that have real functionality and quality work to do. Nothing
in this list blocks anything.

**Scope**
- [ ] Make the JD cards an actual playing-card aspect ratio — they are longer horizontally
      today — then spread them like a ribbon instead of not overlapping at all. Generous, equal
      spacing before analysis, so the start of each title and subtitle is readable. After
      analysis: Apply cards trickled to the left with no overlap, Maybe ribbon-spread in the
      middle at medium overlap, No spread tight on the right at high overlap
- [ ] Card grid sort: once analysis starts, sort by [status_priority, number] instead of number
      alone, so Apply cards float to the top after each `batch_complete` and the user sees which
      JDs survived in real time. Toggle on session status — by number while active, since paste
      order matters during data entry, by status while analyzing or complete. Small change to
      SessionDetailPage's `mergedJds` sort comparator
- [ ] Edit and delete JD cards in `sessions/:id`, reusing the resume card implementation
- [ ] Show the Claude analysis per JD somewhere. There is no place to read it today, and it is
      usually a good chart of skill matches plus a summary
- [ ] "Download all" button — a zip laid out as
      `session_title_timestamp/[company_role_timestamp]/[files]`, so a user who trusts the
      output can take everything at once, open it, check it themselves and apply
- [ ] Add a meta analysis over the tailored resumes — all of them, or at least within one
      session — answering whether tailoring was worth it. Tells me as the dev how worthwhile
      this part of the tool is, and tells the user their money did something beyond what the
      analyze phase already said. Could be as simple as sending the finished resumes and JDs
      through a fresh Claude call and displaying the result in a box
- [ ] Move or duplicate Tab 4's "Batch Tailor All" onto Tab 1 next to Analyze — placement
      decision, not a feature
- [ ] Flag jobs whose JD status changed after tailoring (apply → maybe). They still show on
      Tab 4, which is intentional since the output exists, but a "JD status changed to maybe"
      indicator would explain why it is there
- [ ] Say "Re-analyze" instead of "Analyze" when `session.status === 'complete'`
- [ ] Render MetaAnalysis as markdown. It is whitespace-pre-wrap plain text today, so bold and
      lists would not render — fine while the analysis prompt doesn't ask for markdown, and a
      lightweight renderer is the fix when it does
- [ ] JDPasteForm: auto-populate company and role from the first lines of pasted text (in-code
      TODO), and make that extraction a user-toggleable preference (second in-code TODO)
- [ ] NotFoundPage: update the 404 copy once `/tracking` becomes the index route (ADR-016
      scope). In-code TODO
- [ ] Replace the browser-native `title` tooltip on locked tabs — "Select or create a session to
      unlock this step" — with a custom component. The 1s delay is hardcoded in the browser, not
      in the app, so a component is the only way to make it feel instant
- [ ] Load Inter and JetBrains Mono, or stop naming them. Tailwind's `@theme` references both
      and nothing fetches them, so the app renders in system fonts. Add a `<link>` to index.html
      when typography starts to matter — or never, if system fonts are fine
- [ ] Retry UX on the SessionLayout fetch. A transient error currently means navigating away and
      back; a retry button is the whole fix
- [ ] Loading skeleton or optimistic insert on addJD. The card grid waits for `refreshSession()`
      to resolve, which is fine locally and may not be in production
- [ ] Guard unsaved changes on the resume form. Clicking Edit mid-create silently overwrites
      what was typed
- [ ] Session picker: the /sessions list page is the picker today, and it is simpler and
      sufficient. A nav dropdown was in an old sprint spec and is deferred, not dropped — if it
      comes back it reads from the same `listSessions()` endpoint


---

## Housekeeping (any sprint)

One item, and it is here because it may not survive Phase 1 in this shape.

- [ ] H-1 Build the Activities layer — `routers/activities.py`, `services/activities.py`, and
      the frontend that makes them visible. The data model is already there: Activity table,
      ActivityType enum, and the cascade templates designed in service-layer-notes.md, with
      nothing reading or writing any of it. The core flow (paste → analyze → tailor → download)
      doesn't need it, so it waits for the Full Tracker in the Phase 1 tracking work, which is
      what makes it visible and useful. The README tree and architecture.md already list the
      endpoints as `[ ]` planned
      Design risk: this is the version designed in Phase 0, and the tracker's shape is still
      open. It could be dropped for a different design rather than built as specified, which is
      why it sits here instead of inside a sprint

## Tech Debt (deferred, maybe long term)

Phase 2 and later. Anything that turns out to be Phase 1 belongs in a sprint or in Housekeeping,
not here.

- [ ] T-1 Phase 2+: extract repeated Tailwind class strings into shared component styles
- [ ] T-2 Phase 2+: TailoringPage — extract a `useTailoringData` hook (polling, fetchJobs,
      derivations) when inline chat adds enough complexity that the page's render body obscures
      the JSX. ~15 lines of derivation logic today, which is comfortable, but one more feature
      tips it
- [ ] T-3 Phase 2+: the `failed` error paths in tailoring.py repeat the same 6-line pattern six
      times (set status, add, commit, return). A context manager or decorator would DRY it up.
      Not worth the abstraction at six, worth revisiting if it grows
- [ ] T-4 Phase 2+: `line-clamp-3` depends on `-webkit-line-clamp`, which is non-standard but
      supported in every modern browser. A contingency, not a task: if it ever breaks, fall back
      to JS truncation
- [ ] T-5 Phase 2+: the `jdOverrides` state overlay works but leaves a brief window where
      context jds and overrides can disagree — between stream end and `refreshSession()`
      resolving. Harmless, since the override data matches what the backend wrote; the more
      robust pattern updates the context itself. Revisit if it ever causes a visible bug
- [ ] T-6 Phase 2+: decide what Tab 4 does with jobs whose JD status changed. The batch-tailor
      endpoint only creates jobs for apply-status JDs (backend enforced), but
      `listSessionTailoringJobs` returns every job the session has, so a JD that was "apply"
      when tailored and is "maybe" now still appears. Showing whatever the backend returns is
      the current answer, since the output exists and is useful either way, and the per-JD
      "Tailor" button stays inactive for anything that isn't apply-status without a job. Needs a
      real answer once users reclassify freely
- [ ] T-7 Phase 2+: tests for `scripts/check_docker_context.py` (Level 4 of the overlap check),
      only if the script grows or someone else relies on it. Unit tests for the pure functions
      (probe paths, glob → file name, Dockerfile COPY parsing), plus one Docker test that skips
      when Docker is off. 1–2 files, ~1–2 h
- [ ] T-8 Phase 2+: `--diff` mode for the same script. The check catches shipping files git
      ignores; it does not catch excluding files the app needs. Compare the build context before
      and after a `.dockerignore` edit — done by hand for ea7213e. Until then, a docker build
      plus a smoke test covers that direction
- [ ] T-9 Phase 2+: add the optional per-JD resume picker. Today every resume the user has, up
      to 3, is concatenated into the prompt — `_format_resumes()` in tailoring.py and
      `_resume_block()` in analysis.py — and nothing selects among them, for content or for
      formatting. That default stays, because the model blends across versions in a way a human
      skimming three documents can't. This adds an override, not a new default. Backend:
      optional `resume_ids` body param on the analyze and batch-tailor endpoints, filter the
      resume query when present, fall back to all resumes when absent. Frontend: resume chip
      selector in the Tab 4 kickoff modal, default "All". It would also make `resume_id` on
      TailoringJob mean something — today it stores `resumes[0].id` to satisfy the FK, which
      reads like a choice nobody made.
      Note: `analyzeSession()`, `batchTailor()` and `createTailoringJob()` in client.js were
      scaffolded with exactly this parameter before any endpoint accepted it. The phantom params
      came out in Sprints 10 and 11, so it comes back with real plumbing behind it
- [ ] T-10 Phase 2+: resume snapshots — see ADR-017. A `session_resume_snapshots` table, session
      locking, and a clone-session action, so an analysis references the resume text as it was
      when it ran instead of whatever the resume says today. Costs the ADR follow-through, a new
      table, migrations, service changes and frontend work: a full context window, so it arrives
      as its own sprint rather than as an item
- [ ] T-11 Phase 2+: surface the model in the app, and make it changeable without editing
      code. Today it is `default_model` in config.py, overridable by the `DEFAULT_MODEL` env
      var (README → Choosing the Model). `model_used` is already stored per tailoring job, so
      the data exists and nothing displays it. Cost per model belongs wherever the app/dev
      metrics work lands — if that ships in Phase 1, this is a natural rider on it. Whether the
      *user* picks is a later decision again
- [ ] T-12 Phase 2+: get the system prompts out of the public repo — pick the mechanism
      first, then extract. ADR-013 carries the reasoning: this is IP protection ahead of public
      attention, not functionality. The real gate is traffic rather than a phase boundary —
      decide before the repo gets attention, not after. Two open questions block the work:
      - Where the files live. The README tree says `backend/app/prompts/`; `sync-prompts.sh`
        expects a root `prompts/` (Sprint 15 deletes or fixes that script). Either way,
        `.gitignore` and `.dockerignore` both exclude `prompts` at any depth, so the files would
        reach neither GitHub nor a Docker build.
      - How they reach production. Railway builds from the GitHub snapshot, where git-ignored
        files never exist, so "loaded at startup" needs another route in. ADR-013 lists env vars
        and a private submodule.
      What is actually exposed today, checked 2026-09-16: `ANALYSIS_SYSTEM_PROMPT` in
      `services/analysis.py` (committed 2026-03-04) and `TAILORING_SYSTEM_PROMPT` in
      `services/tailoring.py` (2026-03-05), with `services/claude.py` quoting one in a docstring.
      Both are already in the public history, so extracting them hides future edits, not these
      versions. Public by design and staying that way: `docs/original-prompts.md` and the seeded
      PromptTemplate defaults in `seed.py`.
      Watch: the in-code TODO in `analysis.py` pulls the opposite direction — it would move the
      analysis prompt into the user-editable PromptTemplate table rather than into a file. Those
      are two different futures; pick one before either gets half-built
