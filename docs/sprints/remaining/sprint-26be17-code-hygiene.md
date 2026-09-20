# Code hygiene

**ID**: `[s-26be17]`
**Status**: planned
**Phase**: 1
<!-- was Sprint 16 before ADR-021 -->

**Legs:** timestamps (migration), then the rest (refactor). The timestamp work moves a column
type across ten tables; everything else is a rename or a deletion. One red suite, one cause.

Deprecations, dead files and small corrections, cleared before the next feature lands on top of
them. Nothing here changes behaviour a user would notice, except the timestamps, which are
wrong today.

## leg a — timezone-aware timestamps (migration) --- planned

The `datetime.utcnow()` deprecation, taken as the obvious one-line swap to
`datetime.now(datetime.UTC)`, **breaks prod while the tests stay green**. Every timestamp
column is `sa.DateTime()` — timestamp *without* time zone. asyncpg raises a DataError when an
aware datetime is bound to a naive column, and SQLite silently ignores tzinfo, so the suite
never sees it. [s-26220f] adds token expiry and [s-2716d1] adds purchase history, which is
exactly where the next writer reaches for `datetime.now(UTC)`.

The "timestamps read a day ahead in Oregon" bug is the same bug seen from the frontend — stored
UTC, serialized without an offset, rendered as local. It closes here.

**Done when**
- [ ] all 10 timestamp columns are `timestamptz`: `users.created_at`,
      `users.auth_token_expires_at`, `prompt_templates.created_at`, `resumes.created_at`,
      `sessions.created_at`, `jds.created_at`, `activities.created_at`,
      `activities.completed_at`, `tailoring_jobs.created_at`, `tailoring_jobs.completed_at`
- [ ] models declare them through one `UTCDateTime` type that returns aware UTC datetimes on
      Postgres and SQLite alike, and raises on naive input
- [ ] `grep -rn --include='*.py' utcnow backend/app backend/tests` returns nothing — today
      `models.py` ×7, `tailoring.py:356`, `jds.py:469` (the zip's notes.txt header), and
      `test_tailoring.py` ×4
- [ ] existing rows keep their instant: the ground-truth rows read the same moment before and after
- [ ] every datetime in API JSON carries an offset, and a resume created after 5 PM Pacific
      shows today's date in `ResumeCard`
- [ ] test counts unchanged

**Commits**
| # | | |
|---|---|---|
| 0 | ground truth | On dev, record a few rows' `created_at` values and one resume's rendered date (artifact, not a commit) |
| 1 | new type | Add the `UTCDateTime` TypeDecorator (impl `DateTime(timezone=True)`, attaches UTC on read, raises on naive input) and `utc_now()` to `app/models.py` |
| 2 | migrate | Hand-write the Alembic migration: `op.alter_column(table, col, type_=sa.DateTime(timezone=True), postgresql_using="<col> AT TIME ZONE 'UTC'")` for all 10 columns, and switch the models to `UTCDateTime` and `utc_now` |
| 3 | flip consumers | Call `utc_now()` in `tailoring.py:356`, `jds.py:469`, and the `test_tailoring.py` fixtures |
| 4 | prove equivalence | Confirm the ground-truth rows match, API JSON shows offsets, and the `ResumeCard` date is correct |

**Watch**
- Write the `USING <col> AT TIME ZONE 'UTC'` clause by hand, in upgrade *and* downgrade.
  Without it, Postgres reads existing values in the session's TimeZone setting.
- Push commits 2 and 3 together. Once the models reject naive datetimes, any leftover
  `utcnow()` raises at write time.
- Autogenerate renders `UTCDateTime` by its import path. In this migration and every later one
  ([s-26220f-b], [s-2716d1-b], [s-2716d1-c]), write `sa.DateTime(timezone=True)` instead.
- `DateTime(timezone=True)` alone isn't enough. SQLite still hands back naive datetimes, and
  comparing one to `utc_now()` raises TypeError (reproduced). The decorator's read side is what
  keeps [s-26220f]'s expiry checks testable.
- `users.auth_token_expires_at` is on the list and [s-26220f-b] deletes it. Migrate it anyway: it keeps
  this a single mechanical pass, and skipping it makes the grep-clean done-when a special case.

## leg b — deprecations and dead files (refactor) --- planned

**Kind:** refactor — the suite is the invariant.

**Scope**
- [ ] `HTTP_422_UNPROCESSABLE_ENTITY` deprecation — FastAPI renamed it to
      `HTTP_422_UNPROCESSABLE_CONTENT`. 11 occurrences: jds.py (2), resumes.py (4),
      sessions.py (5). Agents copy the patterns they find, so retire the deprecated name before
      [s-26220f] writes new routes. Done when `grep -rn --include='*.py'
      HTTP_422_UNPROCESSABLE_ENTITY backend/app` returns nothing, the deprecation warning is
      gone from pytest output, and test counts are unchanged
- [ ] Delete `assets/react.svg` and `public/vite.svg` — leftover Vite scaffolding, unreferenced
- [ ] Press Enter to submit the create-session form on SessionsPage.jsx — a simple wrap
- [ ] Clear the tailoring jobs stuck at `queued` from before the `failed` status existed. The
      Sprint 11 migration (`6bc0f4c28a4a`) added `failed` to the TailoringStatus enum but does
      not backfill, so anything queued before it sits there forever. Manual SQL, or delete them
- [ ] Delete `sync-prompts.sh`, or point it at something that exists. It copies a root
      `prompts/` folder into a sibling clone at `../application-pipeline-prompts`; neither
      folder exists on disk, and the private repo `sooperD00/application-pipeline-prompts` holds
      nothing but a `.gitkeep` from three "prompt update" commits on 2026-03-01. The backup it
      implies has never run once. Read the prompt-extraction item in Tech Debt first: if
      extraction picks a different mechanism, this script is the wrong shape anyway and deleting
      it is the honest move
