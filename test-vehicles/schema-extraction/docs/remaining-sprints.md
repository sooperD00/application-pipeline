---
title: Remaining sprints — v2 onboarding
status: living
revised: 2026-07-29
against: samples/human_observations/ (2026-07-27 session), docs/design/
---

# Remaining sprints — v2 onboarding


## Sprint 0 — Use the Extraction Lab to "Finalize" the Schema

- [ ] Housekeeping: duplicate `import prompt as prompt_mod` (`lab.py:37`), stale
      docstring (`lab.py:2`, says `.txt` only), retired model string
      (`README.md:84`)
- [ ] Token summary line counts cached tokens as spent. Guard on
      `not meta["cached"]`.
- [ ] Dollar estimate in the phase-2 gate. Calibration is already in `cost.md`:
      input ≈ chars/1.25 plus the 3,045-char SYSTEM, output ≈ 2.5× input.
- [ ] `ledger.csv` — append one row per fresh call: timestamp, cache_key, name,
      model, in, out, $, seconds, schema_version, prompt_version
- [ ] Index table at the top of `report.html` — one row per document. At 30 docs
      the current report is an unnavigable scroll.
- [ ] Integrate the 07-27 observations into schema v2 (§8)
- [ ] Run a document from each band, read the report, then run the corpus

Exit: one schema version survives a document from each band without producing a new
field request, and the suggested titles are good enough to show a stranger.

---

## Sprint 1 — intake and the high branch

Deployable on its own. Serves the high-score user completely and partially serves
everyone, because Tweaks is available at any score once branching is on gap type.

| Piece | Days |
|---|---|
| Schema v2 finalized, sample runs read | 2 |
| Port `loaders.py` into the app | 0.5 |
| Backend endpoints, profile and bucket tables | 3 |
| **Tweaks widget frontend** | 3–4 |
| Wire to anonymous session and the find-jobs handoff | 1–2 |
| Metadata tracking, minimum: every LLM in/out, and which feedback lane fired | 1–2 |

11–14 focused days. Against a job search as the day job, **3–4 weeks calendar.**
The tracking work is a week on its own if done properly rather than minimally, so
**4–5 weeks** is the real number.

The Tweaks widget is the only new thing in that table. Everything else is a pattern
already running in production.

The estimate breaks if rescore creeps in. Hold it in Sprint 2.

Cost control to design here: several rubric dimensions compute locally with no model
call. Result specificity is "does the bullet contain a number." Result amount is a
count. Structure is "are there recognizable sections." Compute those free and call
the model only for throughline and content judgment. A cheap rescore is a rescore I
can afford to offer freely.

---

## Sprint 2 — Deeps and per-title scoring

Blocked on design. Contains the rescore loop, the per-title score, and the
vault-write path for substantial additions.

Sprint 1 ships instrumented, and its funnel data tells Greg how to build this.

---

