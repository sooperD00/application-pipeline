# Consolidating Railway services into one project

**ID**: `[s-07579b]`
**Status**: planned
**Phase**: 1
<!-- was Sprint 15 before ADR-021 -->

**Kind:** migration — consumer graph: the database, then the callers, then the dev environment.
Why: the app is split across three Railway projects. Private networking stops at the project line, so anything crossing projects goes over public URLs, and forgotten services can keep billing.

Constraints
- Railway can't move services between projects or environments. Recreate each kept service in the home project from the same repo, then retire the old one.
- Delete nothing until its replacement passes its gate.
- If a service uses railway.toml or railway.json, move those settings to the dashboard. Railway stops reading those files 2026-12-01.

0. Pin the ground truth (read-only)
   - Run `railway list` to catch every project, including forgotten ones.
   - For each project and environment: `railway link`, then `railway config pull --json > ~/railway-audit/<project>-<env>.json`.
   - Record per service: repo, root dir, Dockerfile, branch, auto-deploy, up.railway.app URL, database or volume, last deploy, usage cost.
   - Find out why the backend reads DATABASE_PUBLIC_URL.
   - There are two Postgres databases. To find which one DATABASE_PUBLIC_URL points at, match
     the host and port in its value against each database's TCP proxy. Step 1 cannot pick a home
     project until this is answered.
   Gate: every service has a keep, move, or delete call.
1. Pick the home project: the one holding the production database.
   - [ ] Decide the region while you are choosing it, not after. Everything runs in
     asia-southeast1 (Singapore) today, which may be the account's default rather than anyone's
     decision — check whether the plan tier offers a choice at all. A recreated service picks
     its region at creation, so step 2 is the cheap moment to change it, and the database is the
     expensive part: moving it is a dump, a restore and a cutover rather than a setting. If the
     answer is "move", that is its own migration with its own sprint, not a bullet inside this
     one.
2. Recreate each moving service in the home project, next to the old one.
   - Copy its variables. Set the healthcheck path to /health and the builder to Dockerfile.
   Gate: /health returns 200 and the app works end to end on the new service.
3. Flip consumers, one per step.
   - URL (moving services only): remove the up.railway.app name from the old service, then claim it on the new one. Callers and CORS stay unchanged. Expect a short gap between the two.
   - Database: point the backend's database variable at `${{Postgres.DATABASE_URL}}`, the private URL as a reference variable.
   - Any other cross-service URL: make it a reference variable too, so the dev copy in step 5 resolves to dev.
   Gate: logs show traffic only on the new services.
4. Back up every database you're about to delete (pg_dump), even the "garbage" ones.
5. Create the dev environment: `railway environment new dev --duplicate production`.
   - Before approving the staged copy, confirm no variable hard-codes a production URL.
   - Point dev's services at a `dev` branch. Seed dev's database (application-pipeline-dev's backup from step 4 is one source).
   - Watch dev's usage: a full duplicate bills like a second production.
   Gate: dev's frontend calls dev's backend, and dev's backend writes to dev's database.
6. Delete the old services, then the empty projects, application-pipeline-dev included.
   Gate: `railway list` shows one project, and the next usage cycle bills nothing you deleted.

Cleanup
- Update README and docs that name the old projects or URLs.
- Delete ~/railway-audit, or fold its summary into docs.
