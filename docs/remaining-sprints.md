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
> "Entry gate" = work in an *earlier* sprint that a later one leans on, named at the top of the
>   sprint that needs it, as required or recommended. Never a second home: the gate line points
>   at the leg that owns the work and the spec stays there. If a gate item has no owner yet, it
>   is a missing sprint, not a checklist.


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
- Data lifecycle — anonymous retention and anonymous → account conversion land in Sprint 19. A
  delete-my-data path is deferred to public release (19's Out of Scope), which is the honest
  place for it: it is a promise to keep, not a feature to ship early and half-wire
- Terms of service and a privacy policy — due with 20d's go-live commit, which publishes the
  public page Stripe's activation review reads
- Job durability — BackgroundTasks die with the request; architecture.md routes this to
  arq/Redis once users are concurrent
- Railway database backups — Sprint 20's entry gate, since the credit ledger holds paid balances
- Suite health, and whatever tooling this phase warrants for quality and maintainability

**Sprints**

- 13 — Backend dependencies, pip → uv — in progress (13a done, 13b/13c/13d planned)
- 14 — Tests — planned
- 15 — Consolidating Railway services into one project — planned
- 16 — Code hygiene — planned
- 17 — Developer tooling — planned
- 18 — Custom domain — planned
- 19 — User authentication, Google sign-in — planned
- 20 — Billing, and the cost caps it depends on — planned
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
- This Mac has neither venv yet, being a fresh clone. Sprint 17's Makefile is the planned
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
- pin dev down to 3.12 (`uv python pin`, which writes `backend/.python-version`). No Dockerfile
  change, this leg stays single-factor, and it is the cheaper default.
- or bump the image to 3.13. That is a real upgrade of its own and a second factor inside a leg
  that already moves every version — if you want it, it is its own leg, not a line here.
The older note to re-lock with `--python 3.13.7` only holds if the image moves too. (Pulled
from Housekeeping, 2026-09-17, where the skew and the note sat as two separate items.)

Whichever wins, move every consumer in one commit: the Dockerfile base image,
`backend/.python-version`, and Sprint 17's CI pin once that job exists. This is Sprint 19's
entry gate as well as 13c's decision — 19 adds `authlib`, `itsdangerous` and `httpx2`, and new
packages should resolve against one interpreter.

**Done when**
- [ ] dev and the Docker image run the same Python minor version — the decision above, taken
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
  it → Sprint 17 (Developer tooling), which owns the first CI job


---


## Sprint 14 — Tests --- planned

**Legs:** fix the red suite (bugfix), then fill the gaps (feature).

Fill concrete gaps. The goal is confidence before auth (Sprint 19), and before CI, which can't
live on a red suite.

### 14a — restore a green suite (bugfix) --- planned

`tests/test_tailoring.py` has 18 failing tests with one cause, session/DB wiring. They predate
Sprint 13 and were not fixable inside it — the 13a baseline recorded the same 18 before and
after the migration. Until they are green, every "test counts unchanged" done-when in this doc
is measuring a suite that is already red. (Pulled out of Housekeeping, where it was marked for
Sprint 13 — the wrong sprint.)

**Done when**
- [ ] the 18 failures pass, and nothing else changes: 0 failed, same collected count
- [ ] `conftest.py:59` no longer claims `get_current_user` grabs the first User row

**Commits**
| # | | |
|---|---|---|
| 0 | reproduce | Run pytest. `test_list_sessions: assert 0 == 2` is the tell: every request runs as a fresh anonymous user instead of `seeded_user` (artifact, not a commit) |
| 1 | fix | In the `client` fixture, add `app.dependency_overrides[get_current_user] = lambda: seeded_user` beside the `get_session` override. Fix the stale comment |

**Watch** Land after 13c closes. 13c's done-when compares test counts against the 13a baseline,
and this changes them (verified in a scratch copy: 88 passed → 106 passed).

### 14b — fill the gaps (feature) --- planned

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
- [ ] Extract shared test factories and mocks — `__tests__/factories.js` and `__tests__/mocks.js`
      — but only if the same factory or mock has turned up in 3+ test files with an identical
      shape by the time you are in there. Data models have to stabilize first, and this sprint
      is when you find out whether they have.

**Moved out, 2026-09-17.** Three items left this sprint for one that owns them better.
`test_analysis.py` and the six `failed`-path tests in `test_tailoring.py` went to 20a, which
puts the spend paths under test in the sprint where money starts touching them. The
ownership/auth guard test ("session belongs to a different user") went to 19d, where the guard
it tests actually exists — writing it here would have tested a stub.

## Sprint 15 — consolidating Railway services into one project --- planned

sprint type: cutover migration
Why: the app is split across three Railway projects. Private networking stops at the project line, so anything crossing projects goes over public URLs, and forgotten services can keep billing.

Constraints
- Railway can't move services between projects or environments. Recreate each kept service in the home project from the same repo, then retire the old one.
- Delete nothing until its replacement passes its gate.
- If a service uses railway.toml or railway.json, move those settings to the dashboard. Railway stops reading those files 2026-12-01.

0. Pin the ground truth (read-only)
   - Run `railway list` to catch every project, including forgotten ones.
   - For each project and environment: `railway link`, then `railway config pull --json > ~/railway-audit/<project>-<env>.json`.
   - Record per service: repo, root dir, Dockerfile, branch, auto-deploy, up.railway.app URL, database or volume, last deploy, usage cost.
   - Find out why the backend reads DATABASE_PUBLIC_URL.
   Gate: every service has a keep, move, or delete call.
1. Pick the home project: the one holding the production database.
2. Recreate each moving service in the home project, next to the old one.
   - Copy its variables. Set the healthcheck path to /health.
   Gate: /health returns 200 and the app works end to end on the new service.
3. Flip consumers, one per step.
   - URL (moving services only): remove the up.railway.app name from the old service, then claim it on the new one. Callers and CORS stay unchanged. Expect a short gap between the two.
   - Database: point the backend's database variable at `${{Postgres.DATABASE_URL}}`, the private URL as a reference variable.
   - Any other cross-service URL: make it a reference variable too, so the dev copy in step 5 resolves to dev.
   Gate: logs show traffic only on the new services.
4. Back up every database you're about to delete (pg_dump), even the "garbage" ones.
5. Create the dev environment: `railway environment new dev --duplicate production`.
   - Before approving the staged copy, confirm no variable hard-codes a production URL.
   - Point dev's services at a `dev` branch. Seed dev's database (application-pipeline-dev's backup from step 4 is one source).
   - Watch dev's usage: a full duplicate bills like a second production.
   Gate: dev's frontend calls dev's backend, and dev's backend writes to dev's database.
6. Delete the old services, then the empty projects, application-pipeline-dev included.
   Gate: `railway list` shows one project, and the next usage cycle bills nothing you deleted.

Cleanup
- Update README and docs that name the old projects or URLs.
- Delete ~/railway-audit, or fold its summary into docs.

## Sprint 16 — Code hygiene --- planned

**Legs:** timestamps (migration), then the rest (refactor). The timestamp work moves a column
type across ten tables; everything else is a rename or a deletion. One red suite, one cause.

Deprecations, dead files and small corrections, cleared before the next feature lands on top of
them. Nothing here changes behaviour a user would notice, except the timestamps, which are
wrong today.

### 16a — timezone-aware timestamps (migration) --- planned

The `datetime.utcnow()` deprecation, taken as the obvious one-line swap to
`datetime.now(datetime.UTC)`, **breaks prod while the tests stay green**. Every timestamp
column is `sa.DateTime()` — timestamp *without* time zone. asyncpg raises a DataError when an
aware datetime is bound to a naive column, and SQLite silently ignores tzinfo, so the suite
never sees it. Sprint 19 adds token expiry and Sprint 20 adds purchase history, which is
exactly where the next writer reaches for `datetime.now(UTC)`.

The "timestamps read a day ahead in Oregon" bug is the same bug seen from the frontend — stored
UTC, serialized without an offset, rendered as local. It closes here.

**Done when**
- [ ] all 10 timestamp columns are `timestamptz`: `users.created_at`,
      `users.auth_token_expires_at`, `prompt_templates.created_at`, `resumes.created_at`,
      `sessions.created_at`, `jds.created_at`, `activities.created_at`,
      `activities.completed_at`, `tailoring_jobs.created_at`, `tailoring_jobs.completed_at`
- [ ] models declare them through one `UTCDateTime` type that returns aware UTC datetimes on
      Postgres and SQLite alike, and raises on naive input
- [ ] `grep -rn --include='*.py' utcnow backend/app backend/tests` returns nothing — today
      `models.py` ×7, `tailoring.py:356`, `jds.py:469` (the zip's notes.txt header), and
      `test_tailoring.py` ×4
- [ ] existing rows keep their instant: the ground-truth rows read the same moment before and after
- [ ] every datetime in API JSON carries an offset, and a resume created after 5 PM Pacific
      shows today's date in `ResumeCard`
- [ ] test counts unchanged

**Commits**
| # | | |
|---|---|---|
| 0 | ground truth | On dev, record a few rows' `created_at` values and one resume's rendered date (artifact, not a commit) |
| 1 | new type | Add the `UTCDateTime` TypeDecorator (impl `DateTime(timezone=True)`, attaches UTC on read, raises on naive input) and `utc_now()` to `app/models.py` |
| 2 | migrate | Hand-write the Alembic migration: `op.alter_column(table, col, type_=sa.DateTime(timezone=True), postgresql_using="<col> AT TIME ZONE 'UTC'")` for all 10 columns, and switch the models to `UTCDateTime` and `utc_now` |
| 3 | flip consumers | Call `utc_now()` in `tailoring.py:356`, `jds.py:469`, and the `test_tailoring.py` fixtures |
| 4 | prove equivalence | Confirm the ground-truth rows match, API JSON shows offsets, and the `ResumeCard` date is correct |

**Watch**
- Write the `USING <col> AT TIME ZONE 'UTC'` clause by hand, in upgrade *and* downgrade.
  Without it, Postgres reads existing values in the session's TimeZone setting.
- Push commits 2 and 3 together. Once the models reject naive datetimes, any leftover
  `utcnow()` raises at write time.
- Autogenerate renders `UTCDateTime` by its import path. In this migration and every later one
  (19b, 20b, 20c), write `sa.DateTime(timezone=True)` instead.
- `DateTime(timezone=True)` alone isn't enough. SQLite still hands back naive datetimes, and
  comparing one to `utc_now()` raises TypeError (reproduced). The decorator's read side is what
  keeps Sprint 19's expiry checks testable.
- `users.auth_token_expires_at` is on the list and 19b deletes it. Migrate it anyway: it keeps
  this a single mechanical pass, and skipping it makes the grep-clean done-when a special case.

### 16b — deprecations and dead files (refactor) --- planned

**Kind:** refactor — the suite is the invariant.

**Scope**
- [ ] `HTTP_422_UNPROCESSABLE_ENTITY` deprecation — FastAPI renamed it to
      `HTTP_422_UNPROCESSABLE_CONTENT`. 11 occurrences: jds.py (2), resumes.py (4),
      sessions.py (5). Agents copy the patterns they find, so retire the deprecated name before
      Sprint 19 writes new routes. Done when `grep -rn --include='*.py'
      HTTP_422_UNPROCESSABLE_ENTITY backend/app` returns nothing, the deprecation warning is
      gone from pytest output, and test counts are unchanged
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


## Sprint 17 — Developer tooling --- planned

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
- [ ] A first CI job, once the suite is green (Sprint 14), with Railway's Wait for CI turned on
      behind it. `uv lock --check` is a one-line pre-deploy gate with nowhere to run it today,
      and Sprint 19 rewrites the dependency every route uses — a red suite should stop that
      deploy.
      Workflow: `.github/workflows/ci.yml` on `push: branches: [main]`, which is the only
      trigger Railway offers Wait for CI for. Backend `uv lock --check`, `uv sync --locked`,
      `uv run pytest`; frontend `npm ci`, `npm test`. Use `astral-sh/setup-uv`, set
      `working-directory: backend` on every uv step, pin Python to whatever 13c decided and
      Node to 20. Put `python3 scripts/check_docker_context.py --probe` in the same job, since
      `--probe` needs no real ignored files and so works in a fresh clone.
      Prove the gate rather than assuming it: push a deliberately red commit to `main`, confirm
      the Railway deploy shows SKIPPED, then revert and confirm the revert deploys.
      Try the workflow on a branch first — 673f7a0's workflow failed on every push to main.
      Watch: the suite runs on SQLite, so CI cannot see Postgres-only failures like the one
      16a exists to fix. CI proves the tests pass; it does not prove Postgres accepts the
      writes. ~45 min
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


## Sprint 18 — Custom domain --- planned

Move the app to a real hostname before anything external starts pointing at it.
**Kind:** migration — consumer graph: DNS, then the app, then the docs.
**Entry gate:** none. The only sprint in Phase 1 that depends on nothing.

**Why now** Google's OAuth redirect URIs, Stripe's webhook endpoint and the website URL on the
Stripe account are all registered against a host, in three different consoles. Registering them
against `up.railway.app` and moving later means doing all three again, and costs every signed-in
user a fresh sign-in. It is an afternoon plus a registration fee, and it is required before 19c.

**Done when**
- [ ] the app serves over HTTPS at the new domain
- [ ] GET and HEAD requests to the `up.railway.app` URL answer with a 301 to the same path on
      the domain; other methods and `/health` pass through
- [ ] README's "Live at" link points at the domain

**Commits**
| # | | |
|---|---|---|
| 0 | buy and point | Register the domain, add it in Railway, add the DNS records Railway shows, wait for TLS (not a commit) |
| 1 | redirect | Middleware in `main.py`: a GET or HEAD whose host ends in `.up.railway.app` gets a 301 to the same path on the domain; `/health` and other methods pass through |
| 2 | flip the docs | README's "Live at" link |

**Watch**
- Cookies are host-scoped and do not follow the redirect. A tester arriving from the old URL
  starts empty until 19c's sign-in exists. The 30-day cookie has already orphaned most pre-19
  data, so tell testers instead of engineering around it.
- A cheap throwaway name is fine — but rename *before* 19c, never after. Once sign-in lands, a
  rename costs users one sign-in and costs you the three-console checklist above.
- Avoid bargain TLDs if magic links ever become the second way in (19's Out of Scope). Some
  spam filters score them as suspect.


## Sprint 19 — User authentication --- planned

Add Google sign-in on top of per-browser login tokens and CSRF protection, keeping the app
anonymous-first.
**Kind:** feature
**Legs:** extract, migrate, sign in, surface, protect. 19a moves code and 19b moves token
storage, both with behavior fixed. 19c–19d add identity (factor 1: who the user is). 19e rolls
out CSRF (factor 2: request integrity). Merging 19c and 19e means a red suite can't say whether
sign-in or CSRF broke it.
**Entry gate:** 14a (green suite) required before 19a — this sprint rewrites the dependency
every route uses, and a red baseline can't tell you what you broke. Sprint 18 (custom domain)
required before 19c. 13c (one Python), 16 (timestamps and the 422 rename) and 17 (CI behind
Railway's Wait for CI) recommended before 19a.

**Why now** Every browser is its own user, and nothing lets a person reach their data from a
second browser. The cookie is set once, when the user row is created, with a 30-day lifetime
and no refresh. Any tester whose first visit was more than 30 days ago was silently handed a
new, empty user, and their old rows sit in Postgres, unreachable. Sprint 20 also can't sell
credits to an anonymous cookie: a paid balance would die with the cookie.

**Decision** Google sign-in over passwords and over magic links (ADR-019, written in 19a).
Google wins because passwords still need reset and email-verification flows and magic links
need an email provider, a token table and expiry logic — all three need email infrastructure
this project does not have; because Google supplies a verified email; and because there is no
password database to defend once paid credits sit behind the login. Magic links stay on the
table as a *second* way in for people who won't use Google (Out of Scope, below).

**Decides: anonymous retention.** The cookie is 30 days today (`sessions.py:84`, "30 days for
beta") and `auth_token_expires_at` is never set, while `architecture.md` documents 7 days for
anonymous users. Neither survives this sprint as written: 19b moves expiry into `auth_tokens`
and holds it at 30 days unchanged, and 19c makes it slide on use. The 7-day intent was written
for a world where anonymous data expired *because* there was nothing to convert into; sliding
expiry on a browser that can adopt into an account is the better answer. `architecture.md`'s
User table is the doc that changes, at 19b.

**Reference** Two FMH files are checked in beside the sprint notes:
`docs/DEVLOG/sprints/sprint17-18/auth-FMH-not-this-project.py` and
`auth_service-FMH-not-this-project.py`. Read them for the *cookie helper* —
`_set_session_cookies` sets the HTTP-only credential and the JS-readable `csrf_token` together,
which is the pattern 19e ports — and skip the rest: `auth_service.py` is the password design
that lost, and the register/login route shapes don't apply. Also from FMH, not in this repo:
`app/dependencies.py` (`get_current_user`, `csrf_protect`), `app/services/session_service.py`,
the session model, the frontend that reads `csrf_token` and sends `X-CSRF-Token`, and FMH's
ADR-006. Port the session row as source of truth and the synchronizer token; don't copy FMH's
routes.

> Claims below marked "reproduced" or "verified" were checked on 2026-09-16 against a scratch
> copy of this repo at the locked dependency versions. They are findings, not expectations.

### 19a — extract the auth dependency to `app/auth.py` (refactor) --- planned

**Done when**
- [ ] `get_current_user` lives in `backend/app/auth.py`, and `grep -rn --include='*.py' "def get_current_user" backend/app` returns exactly one hit
- [ ] `sessions.py`, `jds.py`, `resumes.py`, and the `client` fixture import it from `app.auth`
- [ ] test counts unchanged from the entry gate
- [ ] behavior unchanged: still one `users.auth_token` per browser

**Commits**
| # | | |
|---|---|---|
| 0 | decide in writing | Write ADR-019 in `decisions.md`: Google sign-in, per-browser hashed tokens, synchronizer CSRF, anonymous-first kept, and passwords and magic links as the runners-up with the reasons |
| 1 | new beside old | Create `app/auth.py` with `get_current_user`; have `sessions.py` re-export it |
| 2 | flip consumers | Point `jds.py`, `resumes.py`, `sessions.py`, and `conftest.py` at `app.auth` |
| 3 | delete the old | Remove the re-export, the "shared auth stub" comments in `jds.py:42` and `resumes.py:27`, and the `main.py:7` docstring line that places auth in `sessions.py` |

**Watch** `app/auth.py` imports only `config`, `database`, and `models`, never a router.
`jds.py` already dodges a circular import with a function-level `settings` import; don't create
a second one.

### 19b — move login tokens to a per-browser table (migration) --- planned

**Done when**
- [ ] an `auth_tokens` table holds one row per browser: `user_id` (FK, cascade delete), `token_hash` (unique), `csrf_token`, `created_at`, `expires_at`, `last_seen_at`
- [ ] every pre-migration `users.auth_token` has a row whose `token_hash` is its SHA-256
- [ ] the ground-truth browser still reaches its data after the migration
- [ ] a new browser gets exactly one `users` row and one `auth_tokens` row
- [ ] no raw token is stored: `users.auth_token` and `users.auth_token_expires_at` are gone
- [ ] existing tests pass with only their `User(auth_token=…)` fixtures edited, and `test_auth.py` covers new, returning, and unknown-token browsers
- [ ] `architecture.md`'s User table matches: both columns gone, `auth_tokens` documented, and the 7-day anonymous note replaced by what 19c actually does

**Commits**
| # | | |
|---|---|---|
| 0 | ground truth | On dev, note a browser's `auth_token` cookie and one of its session IDs (artifact, not a commit) |
| 1 | new beside old | Add the `AuthToken` model and migration. Backfill a row for every existing user: `token_hash`, `csrf_token`, and `expires_at` set to the user's `created_at` plus 30 days, matching the cookie the browser already holds |
| 2 | flip consumer | Make `get_current_user` look up the cookie's SHA-256 in `auth_tokens`; a new browser gets a `users` row plus an `auth_tokens` row with its `csrf_token` |
| 3 | prove equivalence | Confirm the ground-truth cookie still returns its sessions on dev; add `test_auth.py` |
| 4 | delete the old | Drop `users.auth_token` and `users.auth_token_expires_at`. Update every `User(auth_token=…)`: `scripts/seed.py:629`, `conftest.py:49`, `test_sessions.py:37`, `test_tailoring.py:712` |

**Watch**
- `users.auth_token` holds one token per user, so signing in on a phone would rotate it and sign
  the laptop out. That's why tokens move to their own table before sign-in exists.
- Don't name it `sessions`. Search sessions already own `sessions` and `SessionModel`.
- Use SHA-256, not argon2. The token is 32 random bytes, so there's nothing to brute-force, and
  a slow hash on every request would stall the event loop the way FMH's inline argon2 does
  (about 150 ms per verify in a 1-CPU test) — see `auth_service-FMH-not-this-project.py`.
- Backfill in Python inside the migration (few rows), with
  `hashlib.sha256(token.encode()).hexdigest()` and `secrets.token_urlsafe(32)`. Those are the
  same calls `app/auth.py` makes, so the hash can't drift between the migration and the app.
- Keep expiry and cookie lifetime exactly as they are (30 days, never refreshed). Sliding
  expiry is a behavior change and belongs to 19c.

### 19c — Google sign-in (feature) --- planned

**Done when**
- [ ] signing in on a fresh browser keeps that browser's sessions and resumes (the anonymous user is adopted)
- [ ] signing in on a second browser shows the same data on both, and both stay signed in
- [ ] a second browser with its own anonymous data merges it into the account on sign-in, and the emptied anonymous user is deleted
- [ ] a signed-in user who picks a different Google account switches accounts without merging
- [ ] logout deletes only that browser's token row
- [ ] `GET /api/auth/me` returns `email` (null when anonymous) and `is_anonymous`
- [ ] tokens slide in the database: use within the lifetime extends `expires_at` (at most one write a day), and an expired row is rejected
- [ ] a Google account whose `email_verified` is false is refused
- [ ] sign-in works at Sprint 18's domain on Railway, not only on localhost

**Commits**
| # | | |
|---|---|---|
| 0 | configure environments | Create a Google Cloud OAuth web client with redirect URIs `http://localhost:5173/api/auth/google/callback` and `https://<domain>/api/auth/google/callback`. Fill in the consent screen's app name and support email; `openid email profile` needs no Google review. Add the Railway env vars (not a commit) |
| 1 | declare roots | Add `authlib`, `itsdangerous`, and `httpx2` to `[project].dependencies` and re-lock. Add settings `google_client_id`, `google_client_secret`, `session_secret_key`, `public_base_url` |
| 2 | identity column | Add `users.google_sub` (unique, nullable) |
| 3 | sign in | Add `SessionMiddleware`, the Authlib client, and `GET /api/auth/google/login` plus `GET /api/auth/google/callback` with adopt, merge, and switch |
| 4 | token lifecycle | Add `POST /api/auth/logout`, `GET /api/auth/me`, database-side sliding expiry with a long cookie `max_age`, and the server-side expiry check |
| 5 | prove it | Extend `test_auth.py` with `authorize_access_token` mocked: adopt, merge, switch, second browser, logout, expired token, unverified email |

**Watch**
- Set cookies on the `RedirectResponse` the callback returns. A cookie set on an injected
  `Response` is dropped when the route returns a Response object (reproduced on the pinned
  FastAPI). FMH's routes return models, so FMH's pattern breaks here.
- Slide expiry in the database, not the cookie. Give the cookie a long `max_age` (browsers cap
  it near 400 days) and treat `expires_at` as the real expiry. A cookie re-set inside
  `get_current_user` is dropped on routes that return a Response object (analyze, downloads),
  so a cookie-side slide silently fails there.
- Build the callback URL from `settings.public_base_url`, never `request.url_for`. uvicorn
  trusts `X-Forwarded-Proto` only from 127.0.0.1 unless `FORWARDED_ALLOW_IPS` says otherwise
  (verified in uvicorn's source), so behind Railway `url_for` builds an `http://` URL and Google
  rejects the mismatch.
- Use `localhost` everywhere in dev: Vite, the Google console, and `public_base_url`. A stray
  `127.0.0.1` loses the state cookie, and Authlib raises `mismatching_state`.
- Starlette's `SessionMiddleware` names its cookie `session` by default. Rename it
  (`session_cookie="oauth_state"`), give it a short `max_age`, and set `https_only` outside dev.
  It only carries OAuth state.
- Match accounts on Google's `sub`, never on email alone. Only anonymous users are adopted or
  merged, and every sign-in deletes the browser's old token row and issues a fresh one.
- A merge re-parents `sessions`, `resumes`, and `prompt_templates`; JDs, tailoring jobs, and
  activities hang off those. A merge can push someone past 3 resumes, and tailoring already 422s
  above 3, so the user deletes extras.
- Keep only `sub`, `email`, and `email_verified` from Google. Authlib verifies the ID token (a
  JWT) in the callback; store no Google tokens.
- Authlib 1.8 prefers `httpx2` (first on PyPI in May 2026) and doesn't declare it. Without it,
  Authlib falls back to the `httpx` that `anthropic` pulls in and warns. That is the same
  arriving-by-transitive-luck pattern 13d exists to close for greenlet — declare the root.
- FMH's `MeResponse` has `email: str` and `role`. This app needs a nullable `email`,
  `is_anonymous`, and no `role`, or anonymous users get a 500.

### 19d — sign-in in the UI (feature) --- planned

**Done when**
- [ ] the nav shows "Sign in with Google" for anonymous browsers, and the account email plus "Sign out" when signed in
- [ ] signing in lands on `/sessions`, and signing out lands on `/sessions` as a fresh anonymous browser
- [ ] a session URL owned by another user shows the existing "Session not found" state, and a test covers it (the ownership/auth guard item moved here from Sprint 14)
- [ ] existing frontend tests pass

**Commits**
| # | | |
|---|---|---|
| 1 | read identity | Add `getMe()` to `client.js` and a hook that loads it once for the nav. Fix the stale "backend stub grabs the first User row" header comment at `client.js:10` |
| 2 | sign in | Make the nav button a full-page navigation to `/api/auth/google/login` |
| 3 | sign out | Make the nav button POST `/api/auth/logout`, then reload `/sessions` |
| 4 | prove it | Cover both nav states in `App.test.jsx` and another user's session URL in `SessionDetailPage.test.jsx` |

**Watch** Sign-in has to be a full-page navigation. `fetch` can't follow a redirect to Google's
consent screen.

### 19e — CSRF protection (migration) --- planned

Kind is migration because consumers order the commits: issue the token, teach every sender,
then enforce.

**Done when**
- [ ] every POST, PATCH, and DELETE under `/api` returns 403 without a matching `X-CSRF-Token` (Sprint 20's Stripe webhook excepted), and GETs are unaffected
- [ ] the app works end to end in a browser: create a session, paste a JD, analyze (SSE), tailor, download, edit and delete a resume, sign out
- [ ] a browser whose cookie expired mid-page recovers on its next mutation: one 403, one `GET /api/auth/me`, one successful retry
- [ ] domain tests override `csrf_protect` alongside `get_current_user`, and `test_auth.py` exercises the real one

**Commits**
| # | | |
|---|---|---|
| 1 | issue the token | Set a `csrf_token` cookie (JS-readable, Lax, Secure outside dev, no `Domain`) wherever the auth cookie is set — FMH's `_set_session_cookies` is the shape |
| 2 | teach the senders | Have `client.js` read the cookie and send `X-CSRF-Token` from `request()` and `analyzeSession`. Merge per-call headers instead of replacing them. Retry once after a CSRF 403 |
| 3 | enforce | Add `csrf_protect` to `app/auth.py` (skip safe methods, `secrets.compare_digest` against the token row) as a router-level dependency on sessions, jds, resumes, and auth. Add the fixture override for domain tests |
| 4 | prove it | Cover missing, wrong, and correct tokens in `test_auth.py`, plus GET unaffected |

**Watch**
- Ship the senders before the enforcer. A deploy between them 403s every mutation.
- `request()` at `client.js:28` spreads `...options` after `headers`, so today any per-call
  header silently drops Content-Type. Commit 2 has to fix that to send the token at all.
- Give the CSRF 403 a distinct `detail`, so the retry logic doesn't retry other refusals.
- A POST with an expired cookie mints a fresh anonymous row whose token the page doesn't have
  yet. That's the retry path, not a bug.
- FMH exempts register and login because no session exists yet. Here every browser has a token
  row from its first request, so nothing is exempt except Sprint 20's Stripe webhook, which
  lives on its own router without `csrf_protect`.

### Out of Scope (19)
- Magic links for people who won't use Google, as a second way in to the same `users` table → public release
- Returning to the originating page after sign-in needs an allowlisted `next` parameter (open-redirect risk) → H-2
- Rescuing testers' orphaned pre-19 data: re-parent manually after they sign in; their resume text identifies them → H-3
- Deleting an account and its data → public release
- Rate limiting the auth routes: Google absorbs credential attacks, and logout and `/me` are cheap → T-13
- Sprint 17's Makefile and ignore-overlap check are good for this sprint but don't block it → they stay in 17
- **Decide at 19e close:** whether the "`api/client.js` has no retry logic and no token refresh"
  line is now closed. 19e adds the one retry that matters (the CSRF 403 replay), and opaque
  session cookies never need a refresh path — so the argument is that the line is done and
  should be deleted rather than carried. Confirm that in the browser first: if a transient 5xx
  on analyze or tailor still surfaces as an uninterpretable failure, a general retry wrapper is
  a real item and belongs in 20e beside the other client-side work


## Sprint 20 — Billing --- planned

Add prepaid credit billing: meter Claude usage per user, gate spend on a credit balance, and
sell credit packs through Stripe Checkout.
**Kind:** feature
**Legs:** test, meter, charge, sell, then trim the client. 20a puts the spend paths under test
before money touches them. 20b records cost and charges nothing. 20c charges an internal ledger
with no Stripe. 20d connects real payments. 20e is the client-side spend hygiene that has been
waiting for a reason. Each leg can go red for one reason: spend-path behavior, metering, ledger
math, Stripe, or the client.
**Entry gate:** Sprint 19 done; a Stripe account in test mode with its keys in the dev `.env`;
the Stripe CLI installed and logged in; Railway Postgres backups confirmed, since the ledger
will hold paid balances.

**Why now** Users should pay for their own Claude usage, plus a margin. Today every analysis run
(about $1 of Opus, per the July cost screenshot in `docs/cost-tracking/`) and every tailoring job
lands on one API key with no per-user record. `send()` sums input and output tokens, both callers
discard the result (`_tokens` at `analysis.py:252` and `tailoring.py:318`), and `api_cost_cents`
is declared at `models.py:262` and never written. Credit packs amortize Stripe's 30¢ fixed fee
(`cost-notes.txt`) and skip subscription lifecycle states until public release.

### 20a — put the spend paths under test, fix the stuck analysis (bugfix) --- planned

**Done when**
- [ ] `test_analysis.py` covers batching (the 5-JD boundary and a partial final batch), event order (`batch_start`, `jd_result`, `batch_complete`, `analysis_complete`), retry then error, and meta-analysis carried across batches, against a mocked Claude client
- [ ] a test that closes `stream_analysis` mid-run and a test that cancels it during the mocked Claude await both leave the session `active`: red before the fix, green after
- [ ] `test_tailoring.py` covers the six `failed` paths in `run_tailoring_job`: missing JD, missing session, no resumes, no `resume_generation` template, Claude API error, unparseable JSON
- [ ] the claim that an abandoned SSE stream leaves "the backend generator running" is corrected wherever it appears: the backend *does* stop when the client disconnects. The real bug is the session left stuck at `analyzing`, which is what this leg fixes

**Commits**
| # | | |
|---|---|---|
| 0 | reproduce | Close the tab mid-analysis on dev. The session stays `analyzing`, the Analyze button stays disabled, and the endpoint 409s (artifact, not a commit) |
| 1 | pin the behavior | Add `test_analysis.py` happy paths and the two interruption tests; the interruption tests fail |
| 2 | fix | Wrap the analysis loop in `try/finally`. In the `finally`, reset status in a fresh `AsyncSessionLocal()` inside `anyio.CancelScope(shield=True)`. Declare `anyio` in `[project].dependencies`, since it only arrives through Starlette today |
| 3 | confirm | Confirm the interruption tests pass; add the six tailoring `failed`-path tests |

**Watch**
- A plain `finally` doesn't fix this. Starlette cancels the stream through an anyio task group,
  and anyio re-cancels at every `await` inside the cancelled scope, so an unshielded
  `await db.commit()` in the `finally` never finishes. Reproduced on the pinned uvicorn and
  Starlette: the plain `finally` left the status at `analyzing`, and the shielded one reset it.
- The request's `db` can be mid-commit when the cancel lands, so the cleanup opens its own session.
- `docx` generation errors don't fail a tailoring job: the text is still saved and the job goes
  `ready`. 20c decides whether that job is billable.
- `anyio` arriving only through Starlette is the same transitive-luck pattern 13d closes for
  greenlet. Declare it.

### 20b — meter Claude usage per user (feature) --- planned

**Done when**
- [ ] every Claude call that returns writes exactly one `api_usage` row (one per analysis batch, one per tailoring attempt), even when the job fails afterward
- [ ] each row carries `user_id`, the feature, `session_id` or `tailoring_job_id`, `model`, input, output, cache-write, and cache-read tokens, and `cost_micros` (integer micro-dollars)
- [ ] one dev session run on a dedicated API key sums to within a few cents of the Console's cost for that key
- [ ] both `send()` call sites keep the usage object; nothing discards it
- [ ] nothing is charged, and nothing user-facing changes

**Commits**
| # | | |
|---|---|---|
| 1 | carry usage | Make `send()` return the SDK's usage object instead of a summed int (`claude.py:62`); update both callers with behavior unchanged |
| 2 | price it | Add `app/pricing.py`: per-MTok input, output, cache-write, and cache-read prices per model, copied from Anthropic's pricing page with the date. An unknown model raises |
| 3 | record it | Add the `ApiUsage` model and migration. Write rows from `stream_analysis` (per batch, in the batch's commit) and `run_tailoring_job` (per attempt) |
| 4 | prove equivalence | Run one dev session on a dedicated key; compare the summed `cost_micros` with the Console |
| 5 | delete the old | Drop `tailoring_jobs.api_cost_cents` (never written) |

**Watch**
- Add `api_usage` to 19c's merge. Otherwise deleting a merged anonymous user fails on the
  foreign key.
- The analysis conversation re-sends its whole history every batch, so input tokens grow batch
  over batch. Later batches cost more; that's the pricing, not a metering bug.
- The old Sprint 18 scope bullet claimed Sprint 3 "already has per-session cost tracking that
  could be extended." It does not — nothing writes a cost anywhere. That bullet is gone with
  this rewrite; the claim is recorded here so it doesn't get re-derived from the git history.
- `pricing.py` has to know the model id `config.py` actually ships (`default_model`, overridable
  by `DEFAULT_MODEL`), not the one ADR-003 wrote down.

### 20c — credit ledger and spend gate (feature) --- planned

**Done when**
- [ ] a `credit_ledger` row records every grant and debit in integer micro-dollars; balance is `SUM(amount)` per user, and no code path updates or deletes a row
- [ ] for a signed-in user, a completed analysis batch writes one debit linked to its `api_usage` row, a `ready` tailoring job writes one, and a `failed` job writes none
- [ ] analyze, batch-tailor, and single tailor refuse an anonymous browser ("sign in") and a signed-in user below the floor (402, "add credits")
- [ ] `scripts/grant_credits.py` grants credits by email, prints the target database host first, and requires `--yes` outside dev
- [ ] the nav shows the balance, and the Analyze and Tailor buttons explain a 402 and a sign-in refusal
- [ ] `test_credits.py` covers the gate, settlement, failure-is-free, and ledger immutability

**Commits**
| # | | |
|---|---|---|
| 0 | decide in writing | Write ADR-020: the pricing rule (flat per action, or Claude cost × markup), the per-action floors, and whether a `ready` job without a docx is billable |
| 1 | new ledger | Add the `CreditLedger` model and migration, and `balance_for(user_id)` |
| 2 | settle | Debit signed-in users in the same transaction that writes each completed batch's or job's `api_usage` rows. Anonymous spend writes no debit; the gate stops it in commit 5 |
| 3 | comp testers | Add `scripts/grant_credits.py` |
| 4 | show it | Add `GET /api/credits`, the nav balance, and the 402 and sign-in states in `SessionDetailPage` and `TailoringPage` |
| 5 | gate | Add a `require_credits` dependency to the three spend routes: signed in, and balance at or above the floor |
| 6 | prove it | Add `test_credits.py` |

**Watch**
- Grant beta testers credits before the gate deploys, or they hit 402s mid-session.
- The floor check isn't a reservation. Two tabs can start two analyses on one floor's worth of
  credits, and the balance can dip below zero. That's fine at beta scale; lock or reserve if it
  stops being fine.
- Keep the pricing rule in one function (`debit_for(usage)`). The ledger stores micro-dollars
  either way, so flat pricing and cost × markup differ only there.
- 20a's shielded cleanup never debits. Debits belong to completed work only.

### 20d — sell credit packs through Stripe Checkout (feature) --- planned

**Done when**
- [ ] a signed-in user buys a pack in test mode and the balance rises exactly once, including when Stripe resends the event
- [ ] a webhook with a bad signature gets a 400 and writes nothing
- [ ] the webhook route has no cookie auth and no `csrf_protect`, and every other `/api` mutation still has both
- [ ] the success page shows the new balance even when the webhook lands after the redirect
- [ ] live mode stays off until the public page exists and Stripe activates the account

**Commits**
| # | | |
|---|---|---|
| 0 | set up Stripe | Create test-mode products and prices for each pack and a webhook endpoint for `checkout.session.completed` (not a commit) |
| 1 | declare root | Add `stripe[async]` to `[project].dependencies` and re-lock. Add settings for the secret key, webhook secret, and pack price IDs |
| 2 | sell | Add `POST /api/billing/checkout` on a router with `csrf_protect`: create the Checkout Session server-side with `client_reference_id` set to the user ID, and return its URL |
| 3 | fulfill | Add `POST /api/billing/webhook` on its own router. Verify the signature against the raw body, grant on `checkout.session.completed` when `payment_status` is `paid`, and put a unique `stripe_checkout_session_id` on the grant |
| 4 | land | Add the "Add credits" button and the success and cancel pages; the success page polls `/api/credits` |
| 5 | prove it | Add `test_billing.py` with a payload signed by a test webhook secret; run `stripe events resend` on dev for the duplicate case |
| 6 | go live | Publish the public page (business name, service description, support contact, refund and dispute policy, terms of service and privacy policy, reachable without signing in), complete Stripe account activation, and put live keys in Railway |

**Watch**
- Read the raw body (`await request.body()`) before anything parses it. A re-serialized JSON
  body fails signature verification.
- Stripe retries webhooks. Treat the duplicate-key error on `stripe_checkout_session_id` as
  success and return 200, or Stripe keeps retrying.
- `stripe listen` signs forwarded events with its own secret (it prints it), not the dashboard
  endpoint's.
- Use the SDK's async methods (`create_async`), which need the `async` extra. A sync Stripe call
  inside `async def` stalls every SSE stream for the round trip, the same failure as FMH's
  inline argon2.
- The redirect can beat the webhook, so the success page trusts the ledger, not the redirect.
- Creating the Checkout Session server-side from the signed-in user means nobody can credit
  another account by editing a URL parameter.
- Stripe's activation review reads the public page. It has to load without a password and can't
  look under construction.

### 20e — client-side spend hygiene (feature) --- planned

Four client-side items that have been waiting for a reason to be worth doing. The gate in 20c is
that reason: once a retry costs the user money and an abandoned tab costs them a debit, these
stop being politeness and start being correctness.

**Done when**
- [ ] polling backs off instead of hammering. It is 3s forever until terminal today, which is
      chatty if someone leaves the tab open overnight — increase the interval after 60s
- [ ] `analyzeSession()` and the `TailoringPage` polling both take an `AbortController`, and
      `useSSE.abort()` aborts the fetch rather than only cancelling the reader. Note the
      corrected premise from 20a: the backend is not left running forever, but until the fetch
      is actually aborted the server does not see the disconnect, so the abort is what makes
      20a's shielded cleanup fire promptly instead of whenever the socket eventually drops
- [ ] the retry budget has a decided home, written down. The Analyze button re-enables
      immediately on error via `finally { setIsAnalyzing(false) }`, with no retry counter,
      cooldown, or backend cap. 20c's `require_credits` is now the obvious place — confirm that
      is enough, or add a button-level cooldown on top of it
- [ ] **Decide: is the "cap retries on `createTailoringJob`, front end and back" item still
      needed?** It was written when my API key paid for every retry. After 20c the user's own
      balance does, which is the argument for deleting the line — a cap on top of a paid gate
      protects nobody. Delete it if that holds. Keep it if the floor check's non-reservation
      (see 20c's Watch) makes a double-click meaningfully expensive. `tailoring.py` is where the
      backend half would land

**Watch** This leg is frontend-heavy and touches the two pages the rest of the sprint already
changed. Land it last so a red frontend suite means the client, not the ledger.

### Out of Scope (20)
- Subscription with a monthly cap, as a monthly grant row on the same ledger → public release
- Stripe's LLM token billing (private preview), which automates cost × markup → revisit if the pricing rule becomes pure pass-through
- Automated refunds via `charge.refunded`: refund in the Stripe dashboard, then add a negative row with `grant_credits.py` → T-14
- Sales tax and merchant of record (Stripe Managed Payments) → public release decision
- Prompt caching to cut the analysis conversation's growing input cost → T-15
- Free credits for anonymous visitors (the implementation plan's Free Trial Flow) → business rule, public release
- A sweeper that marks stale `processing` tailoring jobs `failed` after a redeploy strands them; the real fix, arq + Redis, is already Phase 1+ in `architecture.md` → H-4
- A Postgres service container in CI, so tests can see Postgres-only failures → T-16
- The rest of Sprint 14 (`test_jds.py` downloads and CRUD, the `TailoringPage` polling test) stays there. Its ownership/auth-guard item moved to 19d, and its analysis and failure-path items moved to 20a


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

Four items. H-1 is here because it may not survive Phase 1 in this shape; H-2 to H-4 are the
shed from planning Sprints 19 and 20 — real work, no sprint earned yet.

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
- [ ] H-2 Return to the originating page after sign-in. A user who opens a session URL while
      signed out lands on `/sessions` instead of where they were going. The fix is a `next`
      parameter, allowlisted to same-origin paths or it is an open redirect. Small, but not
      small enough to bolt onto 19c's callback while adopt, merge and switch are already in
      flight. (From Sprint 19's Out of Scope, 2026-09-17.)
- [ ] H-3 Re-parent the testers' orphaned pre-19 data. The 30-day cookie with no refresh has
      already handed returning testers new empty users, and their old rows sit in Postgres
      unreachable. After they sign in, match on resume text and re-point `sessions`, `resumes`
      and `prompt_templates` at the account. Manual SQL against prod, once per tester — not
      worth automating for seven people, and worth doing while they still remember what they
      pasted. (From Sprint 19's Out of Scope, 2026-09-17.)
- [ ] H-4 Sweep stale `processing` tailoring jobs. A redeploy strands anything mid-flight,
      because BackgroundTasks die with the request, and a stranded job polls forever. Marking
      them `failed` on startup is the cheap fix; the real fix is arq + Redis, already Phase 1+
      in architecture.md. Do the cheap one only once a redeploy actually strands a job someone
      is waiting on. (From Sprint 20's Out of Scope, 2026-09-17.)

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
        expects a root `prompts/` (Sprint 16 deletes or fixes that script). Either way,
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
- [ ] T-13 Phase 2+: rate limit the auth routes. Google absorbs credential attacks — there is no
      password to spray — and `/api/auth/logout` and `/api/auth/me` are cheap. Worth doing when
      there is enough traffic for abuse to cost something. (From Sprint 19's Out of Scope,
      2026-09-17.)
- [ ] T-14 Phase 2+: automated refunds via Stripe's `charge.refunded` webhook. Until then the
      manual path works and is two steps: refund in the Stripe dashboard, then add a negative
      row with `scripts/grant_credits.py`. The ledger is append-only either way. (From Sprint
      20's Out of Scope, 2026-09-17.)
- [ ] T-15 Phase 2+: prompt caching on the analysis conversation. It re-sends its whole history
      every batch, so input tokens grow batch over batch and later batches cost more. Caching
      the stable prefix is the fix. Wait until 20b's `api_usage` rows show what that growth
      actually costs — the cache-write and cache-read token columns are in the schema precisely
      so this is measurable before it is optimized. (From Sprint 20's Out of Scope, 2026-09-17.)
- [ ] T-16 Phase 2+: a Postgres service container in CI. The suite runs on SQLite, so CI cannot
      see Postgres-only failures — the 16a timestamptz class of bug is invisible to a green CI
      run. Worth it once a Postgres-only failure has actually reached prod twice. (From Sprint
      20's Out of Scope, 2026-09-17.)
