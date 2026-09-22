# User authentication

**ID**: `[s-26220f]`
**Status**: planned
**Phase**: 1
<!-- was Sprint 19 before ADR-021 -->

Add Google sign-in on top of per-browser login tokens and CSRF protection, keeping the app
anonymous-first.
**Kind:** feature
**Legs:** extract, migrate, sign in, surface, protect. leg a moves code and leg b moves token
storage, both with behavior fixed. leg c–leg d add identity (factor 1: who the user is). leg e rolls
out CSRF (factor 2: request integrity). Merging leg c and leg e means a red suite can't say whether
sign-in or CSRF broke it.
**Entry gate:** [s-41441e-a] (green suite) required before leg a — this sprint rewrites the dependency
every route uses, and a red baseline can't tell you what you broke. [s-17c7e9] (custom domain)
required before leg c. [s-a75ff1-b] (one Python), [s-26be17] (timestamps and the 422 rename)
and [s-3f291c] (CI behind Railway's Wait for CI) recommended before leg a.

**Why now** Every browser is its own user, and nothing lets a person reach their data from a
second browser. The cookie is set once, when the user row is created, with a 30-day lifetime
and no refresh. Any tester whose first visit was more than 30 days ago was silently handed a
new, empty user, and their old rows sit in Postgres, unreachable. [s-2716d1] also can't sell
credits to an anonymous cookie: a paid balance would die with the cookie.

**Decision** Google sign-in over passwords and over magic links (ADR-019, written in leg a).
Google wins because passwords still need reset and email-verification flows and magic links
need an email provider, a token table and expiry logic — all three need email infrastructure
this project does not have; because Google supplies a verified email; and because there is no
password database to defend once paid credits sit behind the login. Magic links stay on the
table as a *second* way in for people who won't use Google (Out of Scope, below).

**Decides: anonymous retention.** The cookie is 30 days today (`sessions.py:84`, "30 days for
beta") and `auth_token_expires_at` is never set, while `architecture.md` documents 7 days for
anonymous users. Neither survives this sprint as written: leg b moves expiry into `auth_tokens`
and holds it at 30 days unchanged, and leg c makes it slide on use. The 7-day intent was written
for a world where anonymous data expired *because* there was nothing to convert into; sliding
expiry on a browser that can adopt into an account is the better answer. `architecture.md`'s
User table is the doc that changes, at leg b.

**Reference** FMH (Find My Hygienist) is an earlier project of mine with a similar stack and
auth. Two of its files are quarantined in [test-vehicles/FMH/](../../../test-vehicles/FMH/):
`auth-FMH-not-this-project.py` and `auth_service-FMH-not-this-project.py`. Read them for the
*cookie helper* — `_set_session_cookies` sets the HTTP-only credential and the JS-readable
`csrf_token` together, which is the pattern leg e ports — and skip the rest: `auth_service.py` is
the password design that lost, and the register/login route shapes don't apply. Also from FMH,
not in this repo:
`app/dependencies.py` (`get_current_user`, `csrf_protect`), `app/services/session_service.py`,
the session model, the frontend that reads `csrf_token` and sends `X-CSRF-Token`, and FMH's
ADR-006. Port the session row as source of truth and the synchronizer token; don't copy FMH's
routes.

> Claims below marked "reproduced" or "verified" were checked on 2026-09-16 against a scratch
> copy of this repo at the locked dependency versions. They are findings, not expectations.

## leg a — extract the auth dependency to `app/auth.py` (refactor) --- planned

**Done when**
- [ ] `get_current_user` lives in `backend/app/auth.py`, and `grep -rn --include='*.py' "def get_current_user" backend/app` returns exactly one hit
- [ ] `sessions.py`, `jds.py`, `resumes.py`, and the `client` fixture import it from `app.auth`
- [ ] test counts unchanged from the entry gate
- [ ] behavior unchanged: still one `users.auth_token` per browser

**Commits**
| # | | |
|---|---|---|
| 0 | decide in writing | Write ADR-019 as `docs/decisions/adr-019-google-sign-in.md`: Google sign-in, per-browser hashed tokens, synchronizer CSRF, anonymous-first kept, and passwords and magic links as the runners-up with the reasons |
| 1 | new beside old | Create `app/auth.py` with `get_current_user`; have `sessions.py` re-export it |
| 2 | flip consumers | Point `jds.py`, `resumes.py`, `sessions.py`, and `conftest.py` at `app.auth` |
| 3 | delete the old | Remove the re-export, the "shared cookie auth" comments in `jds.py:42` and `resumes.py:27`, and the `main.py:7` docstring line that places auth in `sessions.py` |

**Watch** `app/auth.py` imports only `config`, `database`, and `models`, never a router.
`jds.py` already dodges a circular import with a function-level `settings` import; don't create
a second one.

## leg b — move login tokens to a per-browser table (migration) --- planned

**Done when**
- [ ] an `auth_tokens` table holds one row per browser: `user_id` (FK, cascade delete), `token_hash` (unique), `csrf_token`, `created_at`, `expires_at`, `last_seen_at`
- [ ] every pre-migration `users.auth_token` has a row whose `token_hash` is its SHA-256
- [ ] the ground-truth browser still reaches its data after the migration
- [ ] a new browser gets exactly one `users` row and one `auth_tokens` row
- [ ] no raw token is stored: `users.auth_token` and `users.auth_token_expires_at` are gone
- [ ] existing tests pass with only their `User(auth_token=…)` fixtures edited, and `test_auth.py` covers new, returning, and unknown-token browsers
- [ ] `architecture.md`'s User table matches: both columns gone, `auth_tokens` documented, and the 7-day anonymous note replaced by what leg c actually does

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
  expiry is a behavior change and belongs to leg c.

## leg c — Google sign-in (feature) --- planned

**Done when**
- [ ] signing in on a fresh browser keeps that browser's sessions and resumes (the anonymous user is adopted)
- [ ] signing in on a second browser shows the same data on both, and both stay signed in
- [ ] a second browser with its own anonymous data merges it into the account on sign-in, and the emptied anonymous user is deleted
- [ ] a signed-in user who picks a different Google account switches accounts without merging
- [ ] logout deletes only that browser's token row
- [ ] `GET /api/auth/me` returns `email` (null when anonymous) and `is_anonymous`
- [ ] tokens slide in the database: use within the lifetime extends `expires_at` (at most one write a day), and an expired row is rejected
- [ ] a Google account whose `email_verified` is false is refused
- [ ] sign-in works at [s-17c7e9]'s domain on Railway, not only on localhost

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
  arriving-by-transitive-luck pattern [s-a75ff1-d] exists to close for greenlet — declare the root.
- FMH's `MeResponse` has `email: str` and `role`. This app needs a nullable `email`,
  `is_anonymous`, and no `role`, or anonymous users get a 500.

## leg d — sign-in in the UI (feature) --- planned

**Done when**
- [ ] the nav shows "Sign in with Google" for anonymous browsers, and the account email plus "Sign out" when signed in
- [ ] signing in lands on `/sessions`, and signing out lands on `/sessions` as a fresh anonymous browser
- [ ] a session URL owned by another user shows the existing "Session not found" state, and a test covers it (the ownership/auth guard item moved here from [s-41441e])
- [ ] existing frontend tests pass

**Commits**
| # | | |
|---|---|---|
| 1 | read identity | Add `getMe()` to `client.js` and a hook that loads it once for the nav |
| 2 | sign in | Make the nav button a full-page navigation to `/api/auth/google/login` |
| 3 | sign out | Make the nav button POST `/api/auth/logout`, then reload `/sessions` |
| 4 | prove it | Cover both nav states in `App.test.jsx` and another user's session URL in `SessionDetailPage.test.jsx` |

**Watch** Sign-in has to be a full-page navigation. `fetch` can't follow a redirect to Google's
consent screen.

## leg e — CSRF protection (migration) --- planned

Kind is migration because consumers order the commits: issue the token, teach every sender,
then enforce.

**Done when**
- [ ] every POST, PATCH, and DELETE under `/api` returns 403 without a matching `X-CSRF-Token` ([s-2716d1]'s Stripe webhook excepted), and GETs are unaffected
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
  row from its first request, so nothing is exempt except [s-2716d1]'s Stripe webhook, which
  lives on its own router without `csrf_protect`.

## Out of Scope
- Magic links for people who won't use Google, as a second way in to the same `users` table → public release
- Returning to the originating page after sign-in needs an allowlisted `next` parameter (open-redirect risk) → [h-2e55de]
- Rescuing testers' orphaned data from before [s-26220f]: re-parent manually after they sign in; their resume text identifies them → [h-7451ac]
- Deleting an account and its data → public release
- Rate limiting the auth routes: Google absorbs credential attacks, and logout and `/me` are cheap → [t-0c5fc3]
- [s-3f291c]'s Makefile and ignore-overlap check are good for this sprint but don't block it → they stay in [s-3f291c]
- **Decide at leg e close:** whether the "`api/client.js` has no retry logic and no token refresh"
  line is now closed. leg e adds the one retry that matters (the CSRF 403 replay), and opaque
  session cookies never need a refresh path — so the argument is that the line is done and
  should be deleted rather than carried. Confirm that in the browser first: if a transient 5xx
  on analyze or tailor still surfaces as an uninterpretable failure, a general retry wrapper is
  a real item and belongs in [s-2716d1-e] beside the other client-side work
