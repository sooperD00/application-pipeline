## 1. What this phase delivers

Two artifacts, per user:

1. A **general resume** they would send.
2. An answer to **"what are you, and what do you want to be?"** — a mutable set of
   up to 5 job titles (alternate if this is too hard / low quality: consider a set of REGEX keywords), at phase-0 confidence.

The shipped product needs both before it can run. This phase manufactures them from
whatever the user arrived with: a resume, a CV, a LinkedIn export, or freeform text
typed on the spot, plus iterative, controlled conversation with the user.

The phase ends at the handoff into the find-jobs section. There are 2 options for
the user in the next section, and they shape the deliverables from this section

1. The user can find jobs by searching search strings supplied by Phase 0 into
their preferred job board. They then paste JDs they want to compare into the existing
function of the ApplicationPipeline tool and receive back out apply/maybe/no
recommendation for each JD.
2. Our plan is to implement pull or pull and cache from Common Crawl with set of
beginning URL matches (e.g., the one greenhouse, ashby, and lever) to get company
slugs / names, then a hit the actual APIs to grab open roles, chunked by company slug sets for size management, then to regex against title, then to LLM job details vs
the user job seeker "vault" built in Phase 0. This phase will also contain iterative
conversation option with the user so they can address gaps.

Phase-0 confidence is the bar. The titles and recommended search strings do not have
to be right. They have to be close enough to search on and close enough to argue with.

---

## 2. Out of scope, on purpose

| Not here | Why | Where it lives |
|---|---|---|
| Showing any JD | Intake has no JDs. | find-jobs (shipped) |
| Seniority filtering | Seniority labels don't compare across companies. An executive director makes 40k somewhere and a senior engineer makes 300k somewhere else. It's unreliable inside a single role. No engineer I know uses the seniority filter on any board. | Dropped. Not deferred. |
| Salary filtering | Job searchers accept a wide range depending on what they get out of the job. Some will want a floor. Intake is not where that goes. | Unscheduled |
| SOC / O\*NET codes | Only needed to compare users against each other in a cohort. | Fingerprinting, unscheduled |
| Rescore loops | Unbounded API cost as currently designed. | Sprint 2 |
| A backend for the extraction lab | The schema is still moving. JSON in `out/` costs a version bump; a table costs a migration. | When the schema stops moving |

---

## 3. Titles — the decided position

**Titles are the filter and the vocabulary. They are not the fetch key.**

The manual method that works today, and the one to automate:

1. Pull all open recs from a company.
2. Filter on a title/role regex.
3. LLM the job details section against the resume.

Fetch is per company, via Common Crawl. The Greenhouse public job board API can't
search or filter (`content`, `department_id`, and `office_id` are the only
parameters), so hitting it means pulling an entire board per request.

Step 2 is a regex over a token set, not an exact-title match. A mutable set of 5
decomposes into tokens. Mine: `backend`, `systems`, `platform`, `data`, `engineer`,
and sometimes `streaming`.

Step 2 exists to keep step 3 affordable. The regex is the cost control on the LLM
call, and that is the whole reason it's there.

Titles carry the entire user-facing exchange because they are the only vocabulary
the user shares with the market. That is why the set is mutable and why "close
enough" is the bar.

Caching and fan-out for "find JDs for this person" is its own design. Not this phase.

---

## 4. Decisions made

Don't re-litigate these without new information.

| Decision | Note |
|---|---|
| Branch on **gap type**, not on score | A high-score resume can still be missing content. The 07-27 sample scored `high` and had no result numbers in its own Achievements section. Score sets volume and urgency. It does not pick the widget. |
| The rubric sub-scores generate the Deeps questions | The lowest-scoring dimension picks the question template. `result_specificity: low` produces "how much money did you oversee in \<experience\>?" No separate question-generation prompt. |
| Both widgets stay content-agnostic | See §7. |
| Extraction results stay as JSON files until the schema settles | `test-vehicles/schema-extraction/out/` |
| `claude-opus-5` stays the lab default | One 30-doc pass costs $12. Cheaper models introduce ambiguity I'd then have to rule out before trusting a schema signal. `--model` stays for the deliberate Haiku-vs-Opus disagreement test. |
| `ledger.csv` lives at the lab root, gitignored | Sibling of `DEVLOG.txt` and `cost.md` — durable, human-read, survives `rm -rf out/`. Sample filenames are real people's names, so `cost.md` is the public cost artifact and `ledger.csv` is the private one. Carries a `cache_key` column to join back to `out/.cache/`. |
| Cut `leftover` from the schema | The coverage overlay computes the same thing locally, character-exactly, and deterministically. Two runs gave two different readings of `leftover`, and one contradicted itself. It's a verbatim-quote field, so it's paying output tokens for the least reliable measurement in the rig. |

---

## 5. Open questions

| Question | Owner |
|---|---|
| Low-score branch UX | Greg |
| How the intake agent generates good questions, if the rubric mapping proves insufficient | Greg |
| No-strong-title-match path: does it enter Deeps, and with what questions | Greg |
| Which rubric dimensions compute locally vs need the model | Me — see §6 Sprint 1 |
| Whether raw corpus inputs get committed or stay local | Me |
| Do users agree with the suggested titles, and what closes the gap to titles they want | Deferred past Sprint 2 |

## 7. Widget contracts

Two components. Both are reusable for other kinds of LLM iteration, and both stay
reusable only if they never learn what a resume is.

| | Tweaks | Deeps |
|---|---|---|
| Operates on | Content that is **present** | Content that is **absent** |
| LLM returns | `{before, after, why, target_path}[]` | `{question, why, target_path, priority}[]` |
| User's answer is | accept / reject / counter | new material |
| Terminal action | New resume version, or Add To Vault | Rescore |

`target_path` is where an accepted answer lands: a vault field, a resume bullet
index, a cover-letter paragraph. The LLM returns it and the widget stays dumb. Get
that right and Tweaks works on cover letters and application answers later, and
Deeps works on interview prep and career-changer gap analysis. Get it wrong and both
widgets fork three times.

The feedback lane logs **which** of the three responses fired, not just accept or
reject. "Use this exact instead:" is the user overriding the model in their own
words. That is the highest-value signal in the product.

These two widgets are how the no-direct-chat constraint holds. Every turn is a
schema'd exchange I control, and it still reads as conversation to the user.

---

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

---

## 9. Deferred, with the reason

Kept here so it isn't lost.

**Fingerprinting.** "99% of general counsels have this bullet and you don't." A hard
statistic instead of a model's opinion, and the credibility argument against "just
use ChatGPT." It needs scale, so it waits. The bucket decomposition in Sprint 0 is
its prerequisite, which means the current work is already paying for it.

**SOC / O\*NET as a durable key.** Free-text titles have forty spellings and
fingerprinting needs one. Not needed for the regex filter, so it waits for
fingerprinting.

**Seniority as a scoring input.** Rejected as a filter (§2). A model reading a JD
body can judge whether the scope matches someone's history, and that is a judgment
rather than a string match. If it returns, it returns in the JD-scoring path, not
in intake.

**The funnel visual.** All open jobs, narrowing down to our funnel. Mine to draw.
