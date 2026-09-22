# Housekeeping

Work with no sprint yet. [h-d4b631] is here because it may not survive Phase 1 in this shape;
[h-2e55de], [h-7451ac] and [h-21a0f7] are the shed from planning [s-26220f] and [s-2716d1] —
real work, no sprint earned yet.

IDs are identity, not order: nothing here is renumbered, and the count is what matters. Past
about fifty unassigned items, hold a planning session before adding features.

- [ ] [h-d4b631] Build the Activities layer — `routers/activities.py`, `services/activities.py`, and
      the frontend that makes them visible. The data model is already there: Activity table,
      ActivityType enum, and the cascade templates designed in architecture.md's Activity
      section, with nothing reading or writing any of it. The core flow (paste → analyze →
      tailor → download) doesn't need it, so it waits for the Full Tracker in the Phase 1
      tracking work, which is what makes it visible and useful. architecture.md already lists
      the endpoints as `[ ]` planned
      Design risk: this is the version designed in Phase 0, and the tracker's shape is still
      open. It could be dropped for a different design rather than built as specified, which is
      why it sits here instead of inside a sprint
- [ ] [h-2e55de] Return to the originating page after sign-in. A user who opens a session URL while
      signed out lands on `/sessions` instead of where they were going. The fix is a `next`
      parameter, allowlisted to same-origin paths or it is an open redirect. Small, but not
      small enough to bolt onto [s-26220f-c]'s callback while adopt, merge and switch are already in
      flight. (From [s-26220f]'s Out of Scope, 2026-09-17.)
- [ ] [h-7451ac] Re-parent the testers' orphaned data from before [s-26220f]. The 30-day cookie with no refresh has
      already handed returning testers new empty users, and their old rows sit in Postgres
      unreachable. After they sign in, match on resume text and re-point `sessions`, `resumes`
      and `prompt_templates` at the account. Manual SQL against prod, once per tester — not
      worth automating for seven people, and worth doing while they still remember what they
      pasted. (From [s-26220f]'s Out of Scope, 2026-09-17.)
- [ ] [h-21a0f7] Sweep stale `processing` tailoring jobs. A redeploy strands anything mid-flight,
      because BackgroundTasks die with the request, and a stranded job polls forever. Marking
      them `failed` on startup is the cheap fix; the real fix is arq + Redis, already Phase 1+
      in architecture.md. Do the cheap one only once a redeploy actually strands a job someone
      is waiting on. (From [s-2716d1]'s Out of Scope, 2026-09-17.)
- [ ] [h-0167ce] Decide what happens to sessions as their postings expire. `SessionsPage.jsx`
      has carried the question since Phase 0 with three options and no decision: auto-archive
      after N days, a manual archive or delete button, or a TTL that warns "this session is old,
      postings may be gone". It is a product call before it is a feature, which is why it sat in
      a comment for six months. (Filed from that comment by [s-603d20-c], 2026-09-20.)
- [ ] [h-6e0b18] Put one limit on concurrent Claude calls across all users. Each batch-tailor
      request makes its own `asyncio.Semaphore(tailoring_parallelism)`, so the cap is per request
      rather than per API key: two people tailoring at once run eight calls, and nothing keeps
      the total inside Anthropic's rate limits. It stops being hypothetical the first time two
      people use the app at once. (Filed from service-layer-notes.md when it retired,
      2026-09-21.)
- [ ] [h-a0f0ee] Surface the tailoring strategy. The tailoring prompt asks Claude for `analysis`
      and `strategy` fields, and `run_tailoring_job` keeps them only inside `chat_context`, the
      stored conversation, so nothing shows a user why their resume was tailored the way it was.
      Parse them into columns, or onto the JD's `analysis_text`, when the frontend wants a "why
      these choices" view per job. (Filed from service-layer-notes.md when it retired,
      2026-09-21.)
- [ ] [h-2f37b7] Move the frontend build off Node 20. The Dockerfile's build stage is
      `node:20-slim`, and Node 20 reached end-of-life on 2026-04-30; this Mac runs Node 26, so
      local builds and the image already disagree. Pick the current LTS line (24 today) and move
      the Dockerfile, [s-3f291c]'s CI pin and a declared version (`engines` in package.json, or
      `.nvmrc`) in one commit, then confirm `npm ci`, the build and the suite. Only the build
      stage runs Node — the image that ships is Python — so this is upkeep, not an exposed
      runtime. (Found in the docs review, 2026-09-21.)
- [ ] [h-b37b36] Redact the recipient block in
      `test-vehicles/feedback/asks/2026-03-15-beta-invite.md` — seven names and email addresses,
      one of them a work address, public since `936ed83`. The front matter already records "7",
      so the file loses nothing. Redacting the file does not remove it from the public log, so
      decide separately whether that history gets rewritten. (Moved out of [s-a75ff1], which
      had nothing to do with it, 2026-09-22.)
- [ ] [h-9bbbc0] Recover `test-vehicles/schema-extraction/ledger.py` and narrow the rule that
      swallowed it. That lab's `.gitignore` has `ledger*.*`, which matches the module as well as
      its data files, so the module was never committed and is not in this clone. `lab.py`
      imports it at module level, so the lab cannot start — `--dry-run` included. It should
      still exist on the Windows machine. (Moved out of [s-a75ff1], which had nothing to do with
      it, 2026-09-22.)
