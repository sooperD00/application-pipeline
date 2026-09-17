# Remaining Sprints — Phase 1

LLM MODEL = Claude Opus 5 Max Thinking

TERMINOLOGY
> Execution order: top-down. Next sprint is at the top.
> "Phase" = a body of work with one architecture story.
> "Sprint" = one named change to the system, titled as the category of work.
> "Kind" = commit-ordering heuristic for a leg. [feature | refactor | migration | upgrade]
> "Leg" = sequenced segment of one journey, with an appetite of one sitting
> "Factor" = the class of thing a red suite would blame.
> "Appetite" = sizing rule of one sitting per leg (human); fits in [LLM MODEL] context.
> "Watch" = a known trap.
> "Status" = planned → in progress → done YYYY-MM-DD, or dropped (say why).
> "Housekeeping" = can be added to any sprint; "Tech Debt" = deferred, probably for a while.


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

## Sprint 13 — Backend dependencies --- planned

Migrate backend dependency management from pip to uv.
**Kind:** migration
**Legs:** migration, consumer flip, version upgrade — the first two move packaging (factor 1) with versions pinned; the third moves versions (factor 2) with packaging fixed. Merging the last two means a red suite can't say which.

**Why now** CE! current SWE expectations. Also: requirements.txt is a pip freeze —
13 real roots buried in 20 transitives, hand-appended since. Nothing declares what this
project actually requires, so nothing can be upgraded deliberately.

### 13a — requirements.txt → uv (migration) --- planned

**Done when**
- [x] `uv pip freeze` matches the pre-migration `pip freeze` exactly — same packages,
      same versions, against the commit-0 artifact
- [x] pytest collected count and pass/skip counts are unchanged
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

### 13b — flip the consumers, delete requirements.txt (consumer flip) --- planned

**Done when**
- [ ] `docker build` succeeds installing from pyproject + uv.lock, with no requirements.txt in the repo
- [ ] the built image runs migrations and starts uvicorn
- [ ] image size is same or smaller
- [ ] `grep -rn requirements.txt --exclude-dir=docs --exclude-dir=test-vehicles .` returns nothing

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

### 13c — remove the scaffolding, take the upgrade (version upgrade) --- planned

**Kind:** upgrade

**Done when**
- [ ] constraint-dependencies is gone from pyproject and `uv lock --check` is clean
- [ ] the uv.lock diff has been read, not skimmed — that diff IS the upgrade
- [ ] test counts unchanged
- [ ] docker build + run smoke passes

**Commits**
| # | | |
|---|---|---|
| 1 | remove scaffolding | delete constraint-dependencies, re-lock with upgrades allowed |
| 2 | absorb breakage | whatever the bumps broke — may be zero commits, may be several |

**Watch** sqlmodel is pre-1.0, so any bump is potentially breaking; pydantic, SQLAlchemy and
the anthropic SDK all move fast. If this blows the appetite, cut scope not time: upgrade a
named subset and leave the rest locked.

### Out of Scope (13)
- `python-multipart` has no UploadFile/Form/File usage in app/ — removing it is a second factor → housekeeping
- Declare `sqlalchemy[asyncio]` instead of relying on greenlet arriving transitively → housekeeping
- Delete `backend/venv/` once .venv is trusted — closes the coexistence window locally → housekeeping
- No CI exists. `uv lock --check` is a one-line pre-deploy gate once there's somewhere to run it → techdebt


---


## Sprint N — Tests

Fill concrete gaps. The goal is confidence before adding auth complexity in Sprint 14.

Backend — new files:
- `test_analysis.py`: batching logic (5-JD boundary, partial final batch), SSE event generation (`batch_start`, `jd_result`, `batch_complete`, `analysis_complete`), error/retry with mocked Claude client, meta-analysis accumulation across batches. This is the biggest gap — the core analysis flow has zero dedicated tests.
- `test_jds.py`: zip package download (ADR-014), docx download, JD CRUD (PATCH fields, status override), single-JD tailoring kickoff. Currently only tested indirectly through session-level tests.

Backend — extend existing:
- `test_tailoring.py`: verify the 6 `failed` status paths added in Sprint 11 (missing template, missing JD, missing resumes, Claude API error, JSON parse error, docx generation error). These are the error paths that used to silently bail.

Frontend — extend existing:
- `TailoringPage.test.jsx`: polling lifecycle test (advance fake timers, assert queued→processing→ready transition updates UI). Highest-complexity React test pattern — fake timers + async state + `act()` wrapping. Currently 12 tests cover rendering and button clicks but not the polling state machine.

Frontend — audit:
- Ownership/auth guard tests: verify that session-scoped pages handle "session not found" and "session belongs to different user" (relevant setup for Sprint 14). This is the "multi-user safety" item — make it concrete now even though auth is a stub.

Context load: `test_analysis.py` is the heavy one — analysis.py is 331 lines, the SSE protocol has 4 event types, and the mocked Claude client needs to return structured JSON in batches. The rest are incremental additions to existing test files. Fits one context window.


## Sprint N — Magic link accounts (Phase 1, not scheduled)

Cookie auth shipped in Sprint 12. Anonymous sessions work, data is isolated per browser, beta testers are unblocked.

What's left for real accounts:
1. Magic link flow: email + token, no passwords. Needs an email provider (Resend or SES), a token table, expiry logic.
2. Account conversion: anonymous User row adopts into a permanent account when user enters email. Data carries over — no migration, just set `user.email` and clear the expiry.
3. Frontend: login page, protected routes, auth state management.

Not urgent. Cookie auth covers beta. This becomes relevant when persistence beyond 30 days matters or when users want to switch devices.

---

## Deferred from Phase 0

**Prompts IP** pull the prompts out of the repo. Checked 2026-09-16:
- The two system prompts are string constants: `ANALYSIS_SYSTEM_PROMPT` in `services/analysis.py` (committed 2026-03-04) and `TAILORING_SYSTEM_PROMPT` in `services/tailoring.py` (committed 2026-03-05). `services/claude.py` only mentions one in a docstring. The repo is public, so both are also in its public history; extracting them now hides future edits, not these versions.
- Also public: `docs/original-prompts.md`, and the seeded PromptTemplate defaults in `backend/scripts/seed.py` (public by design, per ADR-013).
- The backup setup was never used. `sync-prompts.sh` copies a root `prompts/` folder into a sibling clone at `../application-pipeline-prompts`, and neither folder exists. The private repo `sooperD00/application-pipeline-prompts` holds only a `.gitkeep` (three "prompt update" commits, all from 2026-03-01).

**Activities** (`routers/activities.py`, `services/activities.py`): The data model is in place (Activity table, ActivityType enum, cascade templates designed in service-layer-notes.md), but no router, service, or frontend exists. The README tree and architecture.md list these as Phase 0 scope, but they aren't needed for the core flow (paste → analyze → tailor → download). Deferring to Phase 1 when the Full Tracker makes them visible and useful.

**Prompts directory** (`backend/app/prompts/`): Placeholder for extracting system prompts from hardcoded strings in `services/analysis.py` and `services/tailoring.py` to files. See ADR-013 — this is about IP protection before the repo gets public attention, not about functionality. Deferred past MVP. Open questions before extracting (found 2026-09-16):
- Where the files live. The README tree says `backend/app/prompts/`, but `sync-prompts.sh` expects a root `prompts/`. Either way, `.gitignore` and `.dockerignore` both exclude `prompts` at any depth, so the files reach neither GitHub nor a Docker build.
- How they reach production. Railway builds from the GitHub snapshot, where git-ignored files never exist, so "loaded at startup" needs another way in (ADR-013 lists env vars and a private submodule).
- The in-code TODO at analysis.py line 56 points the other way: it would move the analysis system prompt into the user-editable PromptTemplate table.

**Resume selection for tailoring.** Phase 0 sends all of the user's resumes (up to 3) to Claude for every analysis and tailoring call. Claude sees all versions and decides what to emphasize, blend, or draw from based on the JD — this is the intended default behavior and should remain the default in all phases. Claude is better and faster at picking the right resume emphasis for a given role than a human skimming three documents, and blending across versions is something a human can't do at all.

Phase 1+ adds an optional override: per-JD resume picker in the Tab 4 kickoff modal where the user can select a single resume or a subset instead of sending all three. Backend changes: add an optional `resume_ids` body param to the analyze and batch-tailor endpoints, filter the resume query when present, fall back to "all resumes" when absent. Frontend: resume chip selector in the tailoring kickoff UI, default state = "All (Claude picks)". The `resume_id` FK on TailoringJob already exists for tracking which resume was primary — Phase 1 makes it meaningful by letting the user constrain the input set.

(Note: `analyzeSession()`, `batchTailor()`, and `createTailoringJob()` in client.js were scaffolded with a `resume_id` parameter anticipating this feature. The backend endpoints never accepted it — they fetch all resumes internally. The phantom params are cleaned up in Sprint 10 (`analyzeSession`) and Sprint 11 (`batchTailor`, `createTailoringJob`) respectively. When resume selection is implemented, the parameter comes back with real plumbing behind it.)

**Resume snapshot architecture** see ADR-017
session_resume_snapshots table, session locking, clone session. Phase 1+.
ADR, a new table, migrations, service changes, and frontend work - a full context window (large sprint).

---

## Housekeeping (any sprint)

- [ ] [SPRINT-13-CLEANUP]: 18 pre-existing failures in tests/test_tailoring.py — session/DB wiring, one cause. Not caused by 13a, not fixable inside it. Route to the Tests sprint.
- [ ] [SPRINT-13-CLEANUP] remember to use `--python 3.13.7` in 13c
- [ ] [SPRINT-14-CLEANUP] H-6 (new): dev/prod interpreter skew. You develop on 3.13.7, you ship on 3.12. This predates the sprint — uv just made it visible. Resolving it means either bumping the image or pinning dev down, and both touch the Dockerfile, so it can't happen before 13b.
- [ ] [SPRINT-14-CLEANUP]: .gitignore/.dockerignore overlap check (pre-commit hook + the .py
      script). The first attempt went to main in 673f7a0, broke the Railway deploy (it also
      moved start.sh), and was reverted in fe8794e. It's parked on branch
      `idea/dockerignore-check` in `test-vehicles/dockerignore-check/`, whose README covers what
      broke, what was learned, and the options. The script is on main now:
      `test-vehicles/dockerignore-check/check_docker_context.py` asks git and Docker directly,
      and `--probe` tests every ignore rule. Left: run it from a pre-commit hook or the
      Makefile. It needs Docker running.
- [ ] `datetime.utcnow()` deprecation warnings — switch to `datetime.now(datetime.UTC)` across models.py (7 occurrences) and tailoring.py (1 occurrence)
- [ ] `HTTP_422_UNPROCESSABLE_ENTITY` deprecation — FastAPI renamed to `HTTP_422_UNPROCESSABLE_CONTENT`. 11 occurrences across jds.py (2), resumes.py (4), sessions.py (5).
- [ ] Timestamps showing 1 day ahead in Oregon (UTC storage, no timezone conversion). Not important for MVP (Nicole is only user), but will confuse anyone else.
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
- [ ] H-1 delete backend/venv/ — after commit 3 is green, not before. The doc already routes
      this to housekeeping, but note that 13a DEPENDS on it: deleting it early does not just
      postpone cleanup, it destroys your ability to prove commit 3. [any sprint after 13a]
- [ ] H-2 remove python-multipart — confirmed zero UploadFile/Form/File usage in app/.
      Second factor, tagged in pyproject.toml. [housekeeping]
- [ ] H-3 declare sqlalchemy[asyncio] — greenlet currently arrives transitively, so nothing
      states this app needs async SQLAlchemy. Second factor, tagged. [housekeeping]
- [x] H-4 .dockerignore does not exclude backend/venv/ (the OLD venv) either. Whether it is
      currently entering the build context depends on the Dockerfile's COPY lines, which I
      did not read. Worth checking in 13b, where "image size is same or smaller" is already
      a done-when — if the old venv has been shipping, that is where the size went. H-1
      makes it moot. [13b]
      Resolved 2026-09-16 in 13a commit 3 (da59650): `.dockerignore` excludes `**/venv` and
      `**/.venv`. Before that, `COPY backend/ .` copied a local backend/venv into local builds
      (Railway never had one, since it's gitignored). For 13b's image-size check, compare
      against a build from da59650 or later.
- [ ] H-5 delete ~/sprint13/ — after 13c, not 13a. 13c re-runs `compare` against the same
      baseline. [after 13c]

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
- [ ] [SPRINT-14-CLEANUP] Makefile wrapping the uv commands — uv binds to an
      environment based on the working directory and says nothing about it (G8; cost an
      hour in 13a when a stale root .venv answered instead of backend/.venv). A recipe
      that cd's first removes the failure mode instead of detecting it.
      Targets: preflight (print sys.prefix, fail unless it ends in backend/.venv), sync,
      test, test-frontend, lock-check (uv lock --check + uv sync --check), seed, run.
      Every uv target depends on preflight.
      Do NOT carry over the 13a/13c scaffolding targets (dep_freeze compare, uv export) —
      they die with their legs.
      Gate: after 13c AND after the mac move. make is not in Git Bash; it arrives with
      the Xcode CLT, which is what makes this worth doing at all.
      Watch: macOS ships GNU make 3.81 (2006 — Apple stopped at the GPLv3 line), so
      `.ONESHELL:` silently does nothing. Each recipe line gets its own shell, so
      `cd backend` on one line does not persist to the next. Write
      `cd backend && uv sync` on one line, or brew a newer make (lands as `gmake` under
      /opt/homebrew unless you add the gnubin path). Getting this wrong reproduces the
      exact bug the Makefile exists to prevent.
      Success condition: it REPLACES typing uv directly. A wrapper used half the time is
      a second way to be in the wrong directory, not a fix.   [techdebt, Sprint 14]
- [ ] T-1 `uv lock --check` as a pre-deploy gate — one line, no CI to put it in. Already in
      the doc's Out of Scope. [Phase N]
- [ ] T-2 requirements.txt CRLF vs LF churn — a .gitattributes entry would stop generated
      files from re-diffing on line endings alone. Only bites for one leg (13b deletes the
      file), so it is probably not worth a commit. Noting it so it is a decision and not an
      oversight. [Phase N or never]