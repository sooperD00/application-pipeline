# Backend dependencies

**ID**: `[s-a75ff1]`
**Status**: in progress
**Phase**: 1
<!-- was Sprint 13 before ADR-021 -->

Migrate backend dependency management from pip to uv.
**Kind:** migration
**Legs:** migration, consumer flip, version upgrade — the first two move packaging (factor 1) with versions pinned; the third moves versions (factor 2) with packaging fixed. Merging the last two means a red suite can't say which.

**Why now** CE! (Copy Exactly!, the Intel sense — match the current SWE standard rather than
invent a local one). Also: requirements.txt is a pip freeze —
41 pinned lines, hand-appended since, in which the 15 packages this app actually asks for (11
runtime, 4 test-only) are indistinguishable from the 26 that came along for the ride. Nothing
declares what this project actually requires, so nothing can be upgraded deliberately.
(Planning guessed 13 roots in 20 transitives; counted at leg a close, it was 15 in 41.)

## leg a — requirements.txt → uv (migration) --- done 2026-09-16

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
| 0a8cbde | doc conflicts fixed (prompts location, spike location, README) |
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
      once leg a closed: the baseline freeze is captured in `docs/DEVLOG/sprints/sprint13/` and
      pushed to the devlog repo, `compare` reads files rather than environments, and neither
      leg b nor leg c consumes the old venv. (Pulled from Housekeeping, 2026-09-17.)
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
      this commit; harmless, and they die with the script in leg c.
      (Pulled from Tech Debt, 2026-09-17, where it was filed as a requirements.txt symptom
      rather than the repo-wide split it turned out to be.)

## leg b — flip the consumers, delete requirements.txt (consumer flip) --- planned

**Prework (in the Railway dashboard, before this leg's first push)**

This leg changes how the image is built, so its deploy is the one that wants the service
configured honestly. Both settings are one visit.

- [ ] Set the healthcheck path to `/health` on application-pipeline. Without one, Railway does
      not wait for the app to answer before sending traffic to a new deploy, and a build that
      succeeds while the app cannot start looks identical from outside.
- [ ] Set the builder to Dockerfile, so the setting says what actually runs. Railway detected
      the Dockerfile on its own when this was first deployed, and an inferred setting is one it
      is free to infer differently later.

[s-07579b] sets both again on every service it recreates, in its step 2. That is not duplicated
work: these are the settings on the service running today, and that service is what gets
replaced there.

**Prework (before the first `uv sync` on a machine)**

uv picks its environment from the directory you run it in and never says which one it picked.
That cost an hour in leg a, when a stale root `.venv` answered instead of `backend/.venv`.

- Run uv from `backend/`. From anywhere else, `uv --directory backend run ...`.
- Check before trusting any number: `uv run python -c "import sys; print(sys.prefix)"` has to
  end in `backend/.venv`.
- There is exactly one `.venv` and it lives in `backend/`. A `.venv` at the repo root is the
  bug, not a second option — delete it rather than working around it.
- Repo-root `scripts/` is stdlib-only by design and needs no venv. Keep it that way: the
  context check has to run exactly when the environment is in doubt.
- This Mac has neither venv yet, being a fresh clone. [s-3f291c]'s Makefile is the planned
  guard (a preflight target that fails unless `sys.prefix` ends in `backend/.venv`).

**Done when**
- [ ] `docker build` succeeds installing from pyproject + uv.lock, with no requirements.txt in the repo
- [ ] the built image runs migrations and starts uvicorn
- [ ] image size is same or smaller — compare against a build from `da59650` or later, never
      anything earlier. Until that commit `.dockerignore` excluded neither `**/venv` nor
      `**/.venv`, so `COPY backend/ .` copied a local backend/venv into local builds and
      whatever size that added is not prod's baseline. Railway never had one, being gitignored
- [ ] `python3 scripts/check_docker_context.py --probe` exits 0 (leg b edits the Dockerfile and `.dockerignore`)
- [ ] `git ls-files --error-unmatch backend/requirements.txt` fails — the file is out of the index
- [ ] `git grep -n requirements.txt -- ':!docs' ':!test-vehicles'` returns nothing. Use `git
      grep`, which reads tracked files only: a plain `grep -rn .` also reads `.git/`, where
      leg b's own delete-commit message will match, plus `backend/.venv` and
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
land*, not requirements.txt, so leg a's inventory missed it. Satisfy it by putting the venv's
bin on PATH in the image rather than rewriting start.sh — fewer files move, and start.sh
stays runnable outside Docker.

**Watch** `.dockerignore`'s `**/.venv` and `**/venv` rules stay after this leg. What leg b
clears is the comment above them, not the rules: `COPY backend/ .` would otherwise copy a host
venv into the image — a macOS venv into a Linux image, or a second one over the image's own.
The `--probe` done-when above is the net that catches it.

## leg c — remove the scaffolding, take the upgrade (version upgrade) --- planned

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
`backend/.python-version`, and [s-3f291c]'s CI pin once that job exists. This is [s-26220f]'s
entry gate as well as leg c's decision — [s-26220f] adds `authlib`, `itsdangerous` and `httpx2`, and new
packages should resolve against one interpreter.

**Done when**
- [ ] dev and the Docker image run the same Python minor version — the decision above, taken
- [ ] constraint-dependencies is gone from pyproject and `uv lock --check` is clean
- [ ] the uv.lock diff has been read, not skimmed — that diff IS the upgrade
- [ ] `dep_freeze.py compare` re-run against the same baseline and its output read. It is
      expected to differ now; that difference is the upgrade stated in package terms
- [ ] test counts: 106 collected − 29 from `test_dep_freeze.py` = 77 collected, with the same
      18 failures in test_tailoring.py (leg a baseline: 106 collected, 88 passed, 18 failed)
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

## leg d — dependency hygiene (refactor) --- planned

**Kind:** refactor — the suite is the invariant.

The two second-factor items leg a tagged and deferred. Both are declaration-only, both move the
lock, and that is why they wait until leg c has read its upgrade diff.

**Done when**
- [ ] `python-multipart` is gone from pyproject and the suite is unchanged — zero
      UploadFile/Form/File usage anywhere in app/, confirmed in leg a
- [ ] `sqlalchemy[asyncio]` is declared, so nothing relies on greenlet arriving transitively
- [ ] `uv lock --check` clean, docker build + run smoke passes
- [ ] no `[SPRINT-a75ff1` markers are left in the repo

**Commits**
| # | | |
|---|---|---|
| 1 | drop a root | remove python-multipart, re-lock |
| 2 | declare a root | `sqlalchemy[asyncio]`, re-lock |

(Pulled from Housekeeping, 2026-09-17, where both sat with no real when.)

## After this sprint closes

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

## Out of Scope
- No CI exists. `uv lock --check` is a one-line pre-deploy gate once there's somewhere to run
  it → [s-3f291c] (Developer tooling), which owns the first CI job
