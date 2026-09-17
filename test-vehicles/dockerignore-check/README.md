# dockerignore-check (parked idea)

A quarantined spike, parked here on main so it stays visible and doesn't get lost. The
parked files never run on their own: GitHub only runs workflows under `.github/workflows/`, and
pre-commit only reads `.pre-commit-config.yaml` at the repo root.

The working check is `scripts/check_docker_context.py`, which is on main. Run it by hand:
`python3 scripts/check_docker_context.py --probe`. When to run it: README Quick Start → Checks.

**Watch:** don't run `sync_dockerignore.py` from here. It works on the repo root, so `--fix`
rewrites the real `.gitignore`, and a default run can rewrite the real `.dockerignore`.

## Why this is here

`.gitignore` says what not to track. `.dockerignore` says what not to ship. Anything git ignores
(secrets, venvs, logs, generated resumes, local databases) should stay out of the Docker build
too. The goal is a check that flags anything git ignores but Docker would still get.

That's harder than diffing the two files, because git and Docker read the same line differently
(see the cheat sheet below). This concern keeps coming back and won't be settled in one session,
so the first attempt and what was learned from it are parked here.

- 2026-09-16: `673f7a0` ("stash: prep for checks on .gitignore and .dockerignore overlaps") put
  the first attempt on main. It broke the deploy (see Problems) and was reverted the same day in
  `fe8794e`.
- 2026-09-16: `0a57dc5` put the comparison script (option 2) on main. `ea7213e` closed the gaps
  it found (option 1): `--probe` went from 398 leaks to 0, and the build context for tracked
  files stayed the same. `df7ad46` taught it to see files inside ignored nested git repos, and
  `c1755c8` moved it to `scripts/`.
- 2026-09-16: this folder first lived on branch `idea/dockerignore-check` (the revert's commit
  message still names it). It moved onto main the same day and the branch was deleted. A
  `test-vehicles/` folder already keeps these files inert, and on main you can see them.

## What's in this folder

| File | Was at (673f7a0) | What it does |
|---|---|---|
| `sync_dockerignore.py` | `scripts/sync_dockerignore.py` | Generates `.dockerignore` from `.gitignore` + a new `.dockerignore.extra`, lints both, then checks for leaks using git |
| `dockerignore.yml` | `.github/workflows/dockerignore.yml` | CI job: `sync_dockerignore.py --check` on every push and pull request |
| `pre-commit-config.yaml` | `.pre-commit-config.yaml` | pre-commit hook: regenerate + leak check on every commit (dot dropped from the name so it's visible here) |

All three are byte-for-byte copies from 673f7a0. That commit also moved `start.sh` and
`sync-prompts.sh` into `scripts/`. Those moves were not carried over.

### How the first attempt works

1. Shared rules live in `.gitignore`. Docker-only rules live in `.dockerignore.extra`.
2. Both files are held to a "dialect" that git and Docker should read the same way: every rule
   starts with `/` or `**/` or has a `/` in the middle, no trailing `/`, no `[...]`, `**` only
   as a whole path segment, no committed nested `.gitignore` files, and no `!` in the extras.
3. `.dockerignore` = a header + `.gitignore` + `.dockerignore.extra`, pasted together.
4. Leak check: `git ls-files --others --ignored` twice, once with git's own rules and once with
   `.dockerignore` as the rule file. Whatever shows up in the first list but not the second
   leaks. This only works because of step 2.

## Problems found (2026-09-16)

What broke on main:

1. **Railway deploy failed.** The Dockerfile does `COPY start.sh .`, and `start.sh` had moved to
   `scripts/`. The revert (`fe8794e`) deployed fine.
2. **CI failed on every push.** `--check` failed its own lint. The current `.gitignore` isn't in
   the dialect (bare names, trailing `/`, `*.py[cod]`), and two nested `.gitignore` files are
   committed.
3. **`pre-commit-config.yaml` is garbled.** Every `key:` colon is missing, and so is the `/` in
   `scripts/sync_dockerignore.py`. YAML reads the whole file as one string. It and
   `dockerignore.yml` also have CRLF line endings.

Design problems in `sync_dockerignore.py`:

4. **It can silently drop Docker-only rules.** If `.dockerignore.extra` doesn't exist, a default
   run rebuilds `.dockerignore` from `.gitignore` alone and exits 0. In a scratch clone that
   removed `.git`, `docs`, `README.md`, `test-vehicles`, `backend/tests`,
   `frontend/src/__tests__` and `**/.mypy_cache`, and all of them went into the build context.
   Fix: refuse to run without the extras file.
5. **The dialect has a hole.** Checked with BuildKit's own context filter (`tonistiigi/fsutil`
   and `moby/patternmatcher` v0.6.1) against git:

   | Rules, in order | git vs Docker | Caught by the script? |
   |---|---|---|
   | `/pkg/**` then `!/pkg/sub` | **differ**: git ignores `pkg/sub/*`, Docker sends it | no: passes the lint and `dead_negations` |
   | `/pkg` then `!/pkg/sub` | differ the same way | yes: `dead_negations` |
   | `/pkg/*` then `!/pkg/sub` | same | n/a |
   | `**/*.pyc` then `!/pkg` | same: `pkg/*.pyc` stays out in both | n/a |

   The leak check reads `.dockerignore` through git, so it can't see the first row.
6. **It's heavy for a simple setup.** `--fix` rewrites 42 lines of `.gitignore` (`*.pyc` becomes
   `**/*.pyc`, `DEVLOG/` becomes `**/DEVLOG`, ...). `*.py[cod]` needs a hand edit. Nested
   `.gitignore` files are banned, including Vite's `frontend/.gitignore` and
   `test-vehicles/schema-extraction/.gitignore`, which should stay self-contained. And there's no
   way to ship something git ignores.
7. **CI can't catch leaks anyway.** A fresh clone has no ignored files, so in CI only the
   "is `.dockerignore` stale" part does anything.

## How big the gap was (probe test, 2026-09-16)

Hand-picked empty files covering each `.gitignore` rule, placed where a real file could land
(71 files, in a scratch clone). Git ignored 69 of them. The hand-written `.dockerignore` still
let Docker send 36:

| Where it lands | Count | Examples |
|---|---|---|
| final image, `/app` (`COPY backend/ .`) | 21 | `*.docx` (tailored resumes), `*.log`, `*.sql.bak`, `pgdata/`, `.coverage`, `htmlcov/`, `*.egg-info/`, `build/`, `dist/`, `app/prompts/`, `.claude/settings.local.json` |
| final image, `/app/static` (Vite copies `frontend/public/` into the build) | 2 | `frontend/public/*.log`, `frontend/public/*.docx` |
| frontend build stage only | 9 | `frontend/.vite/`, `frontend/logs/`, `*.local`, `dist-ssr/` |
| sent as build context, not copied | 4 | root `pgdata/`, `build/`, `dist/`, `.claude/` |

Root cause: a bare name matches at any depth in `.gitignore`, but only at the root in
`.dockerignore`.

**Why this isn't a production emergency:** Railway builds from the GitHub snapshot, and
git-ignored files never exist there. Leaks only happen in local `docker build`s. The real job of
a check is keeping "works in my local image" equal to "works on Railway".

## Cheat sheet: .gitignore vs .dockerignore

| | `.gitignore` | `.dockerignore` |
|---|---|---|
| `name` | any depth | root only, so write `**/name` |
| `/name` | this `.gitignore`'s folder | build-context root (the leading `/` is dropped) |
| `dir/` | directories only | trailing `/` is dropped: file or directory |
| how many files | one per folder, plus `.git/info/exclude` and `~/.config/git/ignore` | one at the build-context root, or `<Dockerfile>.dockerignore` next to the Dockerfile |
| `!` inside an excluded folder | can't re-include | can |
| spaces | leading kept, trailing trimmed | both trimmed |
| case | follows `core.ignorecase` (insensitive on a Mac) | always case-sensitive |
| tracked files | never ignored | Docker doesn't know about git |

## Options

1. **Close the gaps by hand.** Add `**/` rules to `.dockerignore` (`**/*.log`, `**/*.docx`,
   `**/pgdata`, `**/.claude`, ...). Optionally write it as an allowlist (`*`, then `!backend`,
   `!frontend`, `!start.sh`) so only files inside the two app folders can ever leak. Cheap, but
   nothing notices when `.gitignore` grows.
   Status: gaps closed in `ea7213e` (2026-09-16). The allowlist idea wasn't done.
2. **Comparison script** (the direction picked on 2026-09-16). Ask git what it ignores, ask Docker
   what it would send, print the overlap. Neither ignore file gets parsed, so syntax differences
   can't fool it, and both files keep their current style and comments. It runs locally (by
   hand, pre-commit, or a target in the Sprint 14 Makefile) and needs Docker running. A probe
   mode tests every `.gitignore` rule even when no matching file exists yet.
   Status: `scripts/check_docker_context.py` on main (added `0a57dc5`, fixed `df7ad46`, moved
   `c1755c8`). Checked against BuildKit's own context filter (same file list) and a scratch
   clone with 71 junk files. It can't tell that Vite copies `frontend/public/` into the built
   site, so it reports those files as "build stage" only. The next steps (Makefile target, git
   hook, CI, tests) are planned in remaining-sprints.md as levels L1–L4.
3. **The generator in this folder.** The strongest guarantee, and the only option CI can enforce.
   Needs fixes for problems 3 to 5 and the restructuring in 6.
4. **Build from git's file list** (`git ls-files -z ... | tar ... | docker build -`). Matches
   Railway by construction, so there's nothing to check. The catch: every build has to go through
   the wrapper, and docker compose won't. Untested.

## Related

- `docs/remaining-sprints.md`: the Sprint 13a close-out (what happened, commit by commit), and
  the Housekeeping `[SPRINT-14-CLEANUP]` item for this check (levels L0–L4).
- ADR-013 (private prompts): a git-ignored prompt file never reaches a Railway build, so
  extracted prompts need another way into production.
