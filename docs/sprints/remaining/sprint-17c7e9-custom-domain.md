# Custom domain

**ID**: `[s-17c7e9]`
**Status**: planned
**Phase**: 1
<!-- was Sprint 18 before ADR-021 -->

Move the app to a real hostname before anything external starts pointing at it.
**Kind:** migration — consumer graph: DNS, then the app, then the docs.
**Entry gate:** none. The only sprint in Phase 1 that depends on nothing.

**Why now** Google's OAuth redirect URIs, Stripe's webhook endpoint and the website URL on the
Stripe account are all registered against a host, in three different consoles. Registering them
against `up.railway.app` and moving later means doing all three again, and costs every signed-in
user a fresh sign-in. It is an afternoon plus a registration fee, and it is required before [s-26220f-c].

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
  starts empty until [s-26220f-c]'s sign-in exists. The 30-day cookie has already orphaned most
  data from before [s-26220f], so tell testers instead of engineering around it.
- A cheap throwaway name is fine — but rename *before* [s-26220f-c], never after. Once sign-in lands, a
  rename costs users one sign-in and costs you the three-console checklist above.
- Avoid bargain TLDs if magic links ever become the second way in ([s-26220f]'s Out of Scope). Some
  spam filters score them as suspect.
