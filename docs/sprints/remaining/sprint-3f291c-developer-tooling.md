# Developer tooling

**ID**: `[s-3f291c]`
**Status**: planned
**Phase**: 1
<!-- was Sprint 17 before ADR-021 -->

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
- [ ] Decide whether the planning tags are worth a linter yet (ADR-021). Candidates, in the
      order they pay off: every cleanup marker names a sprint or leg that exists; markers naming
      an already-completed sprint are overdue cleanup; `plan.md` lists every file in `remaining/`
      exactly once and every row resolves to a file; the planned order is a topological sort of
      the stated dependencies; and the housekeeping and tech-debt counts get reported, since
      nothing renumbers those lists any more. Suspect lines get printed, not judged — no regex
      can tell a sprint reference from a test count, which is what the tag scheme exists to fix.
      Shape it like `check_docker_context.py`: stdlib-only in `scripts/`, runs from anywhere,
      exit 0 clean / 1 findings / 2 couldn't check, one line in README → Checks.
      Watch: don't write it while the layout is still moving. A linter against a moving spec is
      wasted work, and ADR-021's migration is the thing that has to settle first
- [ ] Port `scripts/readinglist.sh`, or replace it. It came from another project: it slices
      `## Sprint 2C` out of a single plan document and reads `docs/DECISIONS.md` with `D-04a`
      IDs, so it does not run here. After ADR-021's migration its main job is gone — a sprint
      file is already the slice — and what remains is assembling a leg's list from the sprint's
      gates, the ADRs it cites and the files it names. Keep the "WHAT THIS CANNOT SEE" block it
      prints: that block is what makes a generated draft safe to hand to a coding session.
      `docs/reading/reading-list-example.txt` is the shape to aim at
- [ ] Consider a script that closes a sprint, given its ID: the checks and the moves in ADR-021's
      "Close a sprint", printing what it did. `git mv` to `completed/` with the next `<NNN>`
      prefix, the completed-log row in `plan.md`, the marker check, the housekeeping count, and
      the `sprint-<NNN>` tag. It should flag anything it cannot find rather than guess — a file
      whose format drifted is a thing to read, not to repair silently. Grep and sed are enough
      if the formats hold, which is the other reason to keep them boring
