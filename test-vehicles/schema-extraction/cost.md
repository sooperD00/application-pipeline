1. Model default changed — 2.5× cost

Opus 5 is $5/$25 per million input/output tokens

Sonnet 5 is $2/$10 through August 31, 2026, reverting to $3/$15 after that.

the cache invalidates on every SCHEMA_VERSION bump, so each schema iteration re-runs your whole corpus:

| | 30 docs, one pass | × 20 iterations
| Opus 5 | ~$3 | ~$57
| Sonnet 5 (intro) | ~$1.20 | ~$24
| Haiku 4.5 | ~$0.60 | ~$12

Suggestion: keep Sonnet as the default for iterating, pass --model claude-opus-5 for confirmation runs


---

# Intake lab — measured API cost

**Source:** one real run, `Profile.pdf` (LinkedIn export, 6,647 chars extracted),
claude-opus-5, 2026-07-29. Two independent runs, no cache.

## The measurement

| | run A | run B |
|---|---|---|
| input tokens | 5,286 | 5,286 |
| output tokens | 14,882 | 12,554 |

Output runs **~2.5× input** in tokens. Every bucket carries `content` *plus* a
verbatim `source_quote`, so the response is roughly as long as the document.

**Output is ~93% of the cost.** Input is a rounding error.

## Cost per document (6,647 chars)

| model | rate in/out per M | per doc |
|---|---|---|
| Opus 5 | $5 / $25 | **$0.40** |
| Sonnet 5 (intro, thru Aug 31 2026) | $2 / $10 | $0.16 |
| Sonnet 5 (standard, from Sep 1) | $3 / $15 | $0.24 |
| Haiku 4.5 | $1 / $5 | $0.08 |

## Scaling

30-doc corpus. Cache invalidates on every SCHEMA_VERSION / PROMPT_VERSION bump,
so each schema iteration is a full re-run.

| model | one pass | × 20 iterations |
|---|---|---|
| Opus 5 | $12 | $239 |
| Sonnet 5 (intro) | $4.80 | $95 |
| Sonnet 5 (standard) | $7.20 | $143 |
| Haiku 4.5 | $2.40 | $48 |

## Pocket rule

Cost per 1,000 characters of extracted text:

- Opus 5 — **$0.06**
- Sonnet 5 (intro) — $0.024
- Haiku 4.5 — $0.012

## The gate's estimate is wrong

`preview.py` phase 2 said **1,661 input tokens**. Actual was **5,286** — 3.2× off.

Two causes:
1. `CHARS_PER_TOKEN = 4` ignores the SYSTEM prompt (3,045 chars) sent with every call
2. This document tokenizes worse than plain prose (dates, names, line breaks)

It also **doesn't estimate output at all**, which is where nearly all the money is.

Calibration from this run:
- input tokens ≈ chars / 1.25
- output tokens ≈ 2.5 × input tokens

## Caveats

- One document, one format. Not calibrated across the corpus.
- Cached re-runs cost nothing. Only version bumps and edits trigger spend.
- Prompt caching (90% off repeated input) is not implemented here and would
  barely help — the savings are on input, and input isn't the cost.