# schema-extraction (Vault Onboarding / Intake Lab)

This is a throwaway lab pipeline that runs documents through a schema-extraction test with two adjustable components (schema.py and prompt.py) feeding into measurement gates and caching, producing coverage stats and a report.

**Data Path**

`preview.phase1` (stat-only gate, magic-byte sniff) 
  → `loaders.load` 
    → `read_samples` strips the #kind: line 
      → `preview.phase2` (token/truncation gate) 
        → `extract()` (SHA-256 cache over model + both versions + kind + SYSTEM + USER_TEMPLATE + text) 
          → `measure()` 
            → `out/*.json` + the tinted-overlay report.html.

**Questions**

- Q1: **do five bucket types cover a real career document?**
  - role / accomplishment / capability / credential / narrative (/ unclassified)
- A1 (7/30/2026): **Yes**
  - Experiments:
    1. (`claude-opus-5`) (high-score resume) Repeat run with `--no-cache`
      - Same content landing in different bucket means prompt problem, not a schema
      - `Profile.pdf` (general counsel) - high score - had 2 consecutive runs with no meaningful differences
    2. (`claude-opus-5`) (high-score resumes) different resumes bucket fully and reasonably
      - 2 real runs (high-score resumes) `Profile.pdf` (general counsel) and `Carlina*CPG*.docx`
      had solid performance around 90% coverage with minimal unclassified entries
    3. [ ] (`claude-opus-5`) vs (`claude-sonnet-5`) vs (`claude-haiku-4-5-20251001`)
      - do you get the same results with cheaper models? test later when you have good highest \
      model results
      - disagreement about placement means ambiguity in your schema (not in the model)
    4. [ ] The real acceptance test, once the enum looks stable: take the buckets, throw
      the source text away, and feed just the buckets plus a live JD to your existing
      tailoring prompt. If the output holds up against what the blob path produces
      today, the model is right. You already have the control group.

  - What-is-this-called (7/30/2026):
    - Schema v2 is queued in the design doc with several improvements ready to integrate


| `claude-opus-5` stays the lab default | One 30-doc pass costs $12. Cheaper models introduce ambiguity I'd then have to rule out before trusting a schema signal. `--model` stays for the deliberate Haiku-vs-Opus disagreement test. |
| `ledger.csv` lives at the lab root, gitignored | Sibling of `DEVLOG.txt` and `cost.md` — durable, human-read, survives `rm -rf out/`. Sample filenames are real people's names, so `cost.md` is the public cost artifact and `ledger.csv` is the private one. Carries a `cache_key` column to join back to `out/.cache/`. |
| Cut `leftover` from the schema | The coverage overlay computes the same thing locally, character-exactly, and deterministically. Two runs gave two different readings of `leftover`, and one contradicted itself. It's a verbatim-quote field, so it's paying output tokens for the least reliable measurement in the rig. |

## 8. Schema v2 changes

In `test-vehicles/schema-extraction/schema.py`. Bump `SCHEMA_VERSION`.

**Add**

- `resume_category` — Literal over the 19 category names from the 07-22 work. A
  separate axis from `doc_kind`: `doc_kind` is what the document is, `resume_category`
  is what the career is. A Band C academic sends a CV, and those are two facts.
- Rubric sub-scores — structure, content, throughline, result specificity, result
  amount. These replace the single verdict and they generate the Deeps questions.
- `improvements` — the top 1–3–5 things the user can do, as text. Sibling of
  `quality_reasoning`. Accordioned in the UI so an overachiever can take all 5.

**Change**

- `overall_quality` gains a fourth level: `exceptional`.
- Score splits into two axes. General score, plus a per-title score. "Exceptional
  for at least one accepted title" is not expressible as one number.

**Cut**

- `leftover`. See §4.


**Exit Criteria**

- [ ] one schema version survives a document from each band without producing a new
field request, and the suggested titles are good enough to show a stranger.
  - [ ] Q2: what are the 5 bands or resume kinds?
  - [ ] Q3: what is this costing you?
  - [ ] Q4: how are you going to track / report on runs i.e.
    - [ ] Q5: what is your comparability metadata
    - [ ] Q6: what is your quality metric for *user* deliverables?
      - A6 so far: I think the deliverables for intake phase is 
        - [ ] acceptable job titles / roles that the user would be willing to search for and work as
          - this is how the user as a member of society names their interaction structurally with "work" as an insititution
        - [ ] acceptable search keywords or strings or phrases that the user would be willing to search with in their job board of choice, which is tracked in their dashboard and can later give feedback in the funnel analysis which search strings yielded the best results in each funnel step
        - [ ] "success" could be possible with only the `tweaks` feature (looping / feedback to the LLM for *existing* content) for people with "high" quality resumes
        - [ ] `deeps` feature (looping / feedback to the LLM to *generate* new, relevant content with the user) deferred to later
        - [ ] can we get a quick win "optimized" resume + LinkedIn profile suggestions for the user with only the `tweaks` implemented?

housekeeping (7/30/2026):
- [x] The README still references the retired claude-opus-4-8 model string.
- [x] lab.py docstring correctly documents current models, and the sample reading behavior is confirmed
- discrepancy in the README's cache-key documentation that doesn't match what the code actually uses
  - [x] add USER_TEMPLATE to the doc
- `leftover` remains in schema.py even though it was decided to remove it
  - [ ] reconcile DESIGN §4 and §8, `Extraction`, and prompt rule 3
- [ ] Extraction schema also hasn't moved to v2 yet; need to add
  - [ ] resume_category
  - [ ] rubric sub-scores
  - [ ] improvements
  - [ ] SCHEMA_VERSION is still locked at "v1"

## Setup

```bash
# 1. Make sure the venv stays untracked (adds the rule if it got lost in transit)
grep -q '\.venv' .gitignore || echo '.venv/' >> .gitignore  # local .gitignore
grep -q '.env' .gitignore || echo '.env' >> .gitignore  # don't expose your API key

# 2. Build it
python -m venv .venv
source .venv/Scripts/activate    # macOS/Linux: source .venv/bin/activate

# 3. Fill it
python -m pip install -r requirements.txt

# 4. Claude Developer API Key
cp .env.example .env
# add your real key from https://console.anthropic.com/settings/keys to .env
# check you have $ in your account (lower left sidebar): https://console.anthropic.com/settings/cost
```

## Load Samples

Drop files into `samples/`. One person per file, filename becomes the
label. Check `ALLOWED_FILE_TYPES` in loader.py, e.g. `{".txt", ".md", ".pdf", ".docx"}`

In `.txt` files, optional first line hint tells the model what it's looking at: `#kind: cv`.
Use `resume`, `cv`, `linkedin`, `freeform`, `other`. If content disagrees, the model 
overrides.


## Run it

```bash
source .venv/Scripts/activate    # macOS/Linux: source .venv/bin/activate
python lab.py --dry-run     # no key needed, fake extraction, proves the plumbing
python lab.py               # the real thing
```


## The two knobs

| file | what it is |
|---|---|
| `schema.py` | the data model under test — the five types and their fields |
| `prompt.py` | the extraction instructions |

Everything else is measurement. Bump `SCHEMA_VERSION` or `PROMPT_VERSION` when
you change either; that invalidates the cache so you're not reading yesterday's
answers. Unchanged samples don't get re-sent, so iterating on the report itself
is free.

## What the report is measuring

Three numbers, in descending order of how much they should worry you:

**Unclassified count.** The prompt explicitly invites the model to refuse to
classify, and says an honest refusal is more useful than a forced fit. Every
unclassified bucket is a line your enum doesn't cover. Zero across a resume, a
CV, a LinkedIn scrape and a freeform blurb means the five shapes hold. Anything
else, read the `note` — it'll tell you whether you need a sixth type or just a
better prompt.

**Text coverage.** Each bucket has to cite a verbatim span of the source. The
report renders the original document with every claimed character tinted by the
bucket that took it, and leaves the rest red. Uncovered text is content that
would silently vanish from someone's vault. This is the part to show a person
rather than describe to them.

**Quotes not found in source.** The model cited text that isn't in the
document. Either it drifted while copying or it invented content, and both are
worth knowing before you trust anything else on the page.

## Why every schema field is required

Structured outputs compile the schema into a sampling grammar, and the API caps
a request at 24 optional parameters and 16 union-typed ones. `Optional[str]`
counts as a union, so the natural Python spelling of this schema blows both
budgets and returns *"Schema is too complex for compilation."* Hence: everything
required, absence is `""`. Ugly in Python, cheap in grammar, and it stops being
your problem the moment this lands in SQLModel.

Docs: https://platform.claude.com/docs/en/build-with-claude/structured-outputs


## How the caching works

The key is a SHA-256 of six things joined together. The filename is not one of them.
Reasoning: the cache is keyed onwhat would be sent to the API.

```text
0: claude-opus-5          ← --model
1: v1                     ← PROMPT_VERSION
2: v1                     ← SCHEMA_VERSION
3: unknown                ← the #kind: line
4: SYSTEM (3,045 chars)   ← the whole system prompt, verbatim
5: the extracted text
6: USER_TEMPLATE
```

Verified — same PDF under two names:

```text
Profile.pdf  -> 5bc54aacc0242031.json
RENAMED.pdf  -> 5bc54aacc0242031.json
same key: True
```