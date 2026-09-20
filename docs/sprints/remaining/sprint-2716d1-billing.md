# Billing

**ID**: `[s-2716d1]`
**Status**: planned
**Phase**: 1
<!-- was Sprint 20 before ADR-021 -->

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

## 20a — put the spend paths under test, fix the stuck analysis (bugfix) --- planned

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

## 20b — meter Claude usage per user (feature) --- planned

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

## 20c — credit ledger and spend gate (feature) --- planned

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

## 20d — sell credit packs through Stripe Checkout (feature) --- planned

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

## 20e — client-side spend hygiene (feature) --- planned

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

## Out of Scope (20)
- Subscription with a monthly cap, as a monthly grant row on the same ledger → public release
- Stripe's LLM token billing (private preview), which automates cost × markup → revisit if the pricing rule becomes pure pass-through
- Automated refunds via `charge.refunded`: refund in the Stripe dashboard, then add a negative row with `grant_credits.py` → T-14
- Sales tax and merchant of record (Stripe Managed Payments) → public release decision
- Prompt caching to cut the analysis conversation's growing input cost → T-15
- Free credits for anonymous visitors (the implementation plan's Free Trial Flow) → business rule, public release
- A sweeper that marks stale `processing` tailoring jobs `failed` after a redeploy strands them; the real fix, arq + Redis, is already Phase 1+ in `architecture.md` → H-4
- A Postgres service container in CI, so tests can see Postgres-only failures → T-16
- The rest of Sprint 14 (`test_jds.py` downloads and CRUD, the `TailoringPage` polling test) stays there. Its ownership/auth-guard item moved to 19d, and its analysis and failure-path items moved to 20a
