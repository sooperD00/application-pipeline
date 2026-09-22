# ADR-018: uv for Backend Dependency Management

**Date**: 2026-08-30 (recorded 2026-09-17, after the first leg landed)
**Status**: Accepted — [s-a75ff1-a] shipped 2026-09-16; [s-a75ff1-b], [s-a75ff1-c] and [s-a75ff1-d] planned

**Decision**: Declare backend dependencies in `backend/pyproject.toml`, resolve and lock them with uv, and commit `uv.lock`. `requirements.txt` becomes generated output for one leg of the migration, then is deleted once the Dockerfile installs from the lock.

**Rationale**: `requirements.txt` was a `pip freeze` — 41 pinned lines, hand-appended over months, in which the 15 packages this app actually asks for (11 runtime, 4 test-only) were indistinguishable from the 26 that merely came along. Nothing in the repo stated what the project requires, so nothing could be upgraded deliberately: every pin looked equally load-bearing and equally unexplained. Declaring roots separates "what this app needs" from "what that implies", and that separation is what makes an upgrade reviewable instead of a gamble.

Choosing uv specifically: it reads a PEP 621 `[project]` table, so the declaration is tool-agnostic and survives a later change of tool — the lockfile is the only uv-shaped artifact in the repo. It also manages the interpreter, which matters here because dev and prod disagree about the Python version. Matching current practice was itself part of the reason: this is a public repo that doubles as evidence of how I work.

**Structure**: The migration is split into legs so a red suite can name what broke. Packaging moves first with versions pinned ([s-a75ff1-a]), then the consumers ([s-a75ff1-b]), then versions with packaging fixed ([s-a75ff1-c]), then two deferred declaration changes ([s-a75ff1-d]). A `[tool.uv] constraint-dependencies` block holds every package at the pre-migration freeze until [s-a75ff1-c] deletes it — that diff *is* the upgrade. [s-a75ff1] has the leg-by-leg plan; docs/sprints/plan.md says where it lives.

**Consequences**:
- A generated `requirements.txt` outlives the migration by one leg, so the Docker build keeps working while packaging changes underneath it.
- Two virtualenvs coexist locally during [s-a75ff1-a] — the old `backend/venv` and uv's `backend/.venv`. The old one was deleted once [s-a75ff1-a] closed and the baseline freeze was safely captured.
- Dev/prod interpreter skew became visible rather than new: 3.13.7 locally, 3.12 in the image. [s-a75ff1-c] has to pick one before it re-locks, since reading an upgrade diff on an interpreter nobody deploys proves little.
- uv binds to an environment based on the working directory and does not say which one it picked. That cost an hour in [s-a75ff1-a], when a stale root `.venv` answered instead of `backend/.venv`. The by-hand guards are in [s-a75ff1-b]'s prework; a Makefile preflight target is the planned fix.

**Alternatives considered**:
- **Stay on `pip freeze`.** No migration cost, but the problem being solved is precisely that a freeze cannot tell a root from a transitive.
- **pip-tools** (`requirements.in` → `requirements.txt`): declares roots, keeps pip, smaller move. Not chosen — it leaves interpreter management unsolved and offers no project manifest to grow into.
- **Poetry or PDM**: both declare and lock. Not chosen over uv, and because the declaration lives in PEP 621 fields rather than tool-specific ones, switching later costs a re-lock rather than a rewrite.

**Update 2026-09-21** — the interpreter skew is settled: dev pins 3.12, the version the image already runs, through `backend/.python-version`, written in [s-a75ff1-b]. The move from the Windows machine to a Mac had widened the skew (the Mac's default is Homebrew 3.14.3), and pinning before the Mac's first `uv sync` means it never has a mismatched venv. The lock was never the problem, since uv resolves one lock for every supported Python. The risk was code that runs on a newer interpreter and not on the one prod runs. A newer Python is its own change: the Dockerfile and `.python-version` move together.
