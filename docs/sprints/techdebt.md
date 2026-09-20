# Tech Debt

Phase 2 and later. Anything that turns out to be Phase 1 belongs in a sprint or in Housekeeping,
not here.

- [ ] [t-5005a3] Phase 2+: extract repeated Tailwind class strings into shared component styles
- [ ] [t-b1137e] Phase 2+: TailoringPage — extract a `useTailoringData` hook (polling, fetchJobs,
      derivations) when inline chat adds enough complexity that the page's render body obscures
      the JSX. ~15 lines of derivation logic today, which is comfortable, but one more feature
      tips it
- [ ] [t-03c13e] Phase 2+: the `failed` error paths in tailoring.py repeat the same 6-line pattern six
      times (set status, add, commit, return). A context manager or decorator would DRY it up.
      Not worth the abstraction at six, worth revisiting if it grows
- [ ] [t-2a07b4] Phase 2+: `line-clamp-3` depends on `-webkit-line-clamp`, which is non-standard but
      supported in every modern browser. A contingency, not a task: if it ever breaks, fall back
      to JS truncation
- [ ] [t-edd486] Phase 2+: the `jdOverrides` state overlay works but leaves a brief window where
      context jds and overrides can disagree — between stream end and `refreshSession()`
      resolving. Harmless, since the override data matches what the backend wrote; the more
      robust pattern updates the context itself. Revisit if it ever causes a visible bug
- [ ] [t-f4e26b] Phase 2+: decide what Tab 4 does with jobs whose JD status changed. The batch-tailor
      endpoint only creates jobs for apply-status JDs (backend enforced), but
      `listSessionTailoringJobs` returns every job the session has, so a JD that was "apply"
      when tailored and is "maybe" now still appears. Showing whatever the backend returns is
      the current answer, since the output exists and is useful either way, and the per-JD
      "Tailor" button stays inactive for anything that isn't apply-status without a job. Needs a
      real answer once users reclassify freely
- [ ] [t-de0b6b] Phase 2+: tests for `scripts/check_docker_context.py` (Level 4 of the overlap check),
      only if the script grows or someone else relies on it. Unit tests for the pure functions
      (probe paths, glob → file name, Dockerfile COPY parsing), plus one Docker test that skips
      when Docker is off. 1–2 files, ~1–2 h
- [ ] [t-e5a33d] Phase 2+: `--diff` mode for the same script. The check catches shipping files git
      ignores; it does not catch excluding files the app needs. Compare the build context before
      and after a `.dockerignore` edit — done by hand for ea7213e. Until then, a docker build
      plus a smoke test covers that direction
- [ ] [t-356ac5] Phase 2+: add the optional per-JD resume picker. Today every resume the user has, up
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
- [ ] [t-4baae5] Phase 2+: resume snapshots — see ADR-017. A `session_resume_snapshots` table, session
      locking, and a clone-session action, so an analysis references the resume text as it was
      when it ran instead of whatever the resume says today. Costs the ADR follow-through, a new
      table, migrations, service changes and frontend work: a full context window, so it arrives
      as its own sprint rather than as an item
- [ ] [t-a2266c] Phase 2+: surface the model in the app, and make it changeable without editing
      code. Today it is `default_model` in config.py, overridable by the `DEFAULT_MODEL` env
      var (README → Choosing the Model). `model_used` is already stored per tailoring job, so
      the data exists and nothing displays it. Cost per model belongs wherever the app/dev
      metrics work lands — if that ships in Phase 1, this is a natural rider on it. Whether the
      *user* picks is a later decision again
- [ ] [t-84a71a] Phase 2+: get the system prompts out of the public repo — pick the mechanism
      first, then extract. ADR-013 carries the reasoning: this is IP protection ahead of public
      attention, not functionality. The real gate is traffic rather than a phase boundary —
      decide before the repo gets attention, not after. Two open questions block the work:
      - Where the files live. The README tree says `backend/app/prompts/`; `sync-prompts.sh`
        expects a root `prompts/` ([s-26be17] deletes or fixes that script). Either way,
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
- [ ] [t-0c5fc3] Phase 2+: rate limit the auth routes. Google absorbs credential attacks — there is no
      password to spray — and `/api/auth/logout` and `/api/auth/me` are cheap. Worth doing when
      there is enough traffic for abuse to cost something. (From [s-26220f]'s Out of Scope,
      2026-09-17.)
- [ ] [t-8be739] Phase 2+: automated refunds via Stripe's `charge.refunded` webhook. Until then the
      manual path works and is two steps: refund in the Stripe dashboard, then add a negative
      row with `scripts/grant_credits.py`. The ledger is append-only either way. (From Sprint
      [s-2716d1]'s Out of Scope, 2026-09-17.)
- [ ] [t-ec7c6c] Phase 2+: prompt caching on the analysis conversation. It re-sends its whole history
      every batch, so input tokens grow batch over batch and later batches cost more. Caching
      the stable prefix is the fix. Wait until [s-2716d1-b]'s `api_usage` rows show what that growth
      actually costs — the cache-write and cache-read token columns are in the schema precisely
      so this is measurable before it is optimized. (From [s-2716d1]'s Out of Scope, 2026-09-17.)
- [ ] [t-7d6ef0] Phase 2+: a Postgres service container in CI. The suite runs on SQLite, so CI cannot
      see Postgres-only failures — the [s-26be17-a] timestamptz class of bug is invisible to a green CI
      run. Worth it once a Postgres-only failure has actually reached prod twice. (From Sprint
      [s-2716d1]'s Out of Scope, 2026-09-17.)
