# Phase 0: Onboarding / Job Seeker Intake

For each user

## Input

- Resume(s) / CV / LinkedIn Profile / freeform text typed on the spot
- Desired job titles or roles (optional)

Titles carry the entire user-facing exchange because they are the only 
vocabulary the user shares with the market. That is why the set is mutable 
and why "close enough" is the bar.

Not used: 
- Seniority filtering: labels don't compare across companies
- Salary filtering: job seekers accept a wide range; add a floor later (Unscheduled)
- SOC / O\*NET codes: need to RNU more before decide how to use these (first look 
during `test-vehicle/schema-extraction/` experiementation)
  - useful for "resume type?"
  - useful define comparability groups?

## Explore

Iterative, controlled conversation with the user, guided to draw out
information prioritized by what will strengthen the candidate's job
seeking materials.

Content-agnostic components for:
**Tweaks**: suggest / feedback / accept loops to ++ existing content
**Deeps**: suggest / feedback / accept loops to surface new content

Rescore loop implementation is currently unknown - we will explore in
the Sprint 1. Unbounded API cost as currently designed, design in progress.

## Deliver

An optimized **general resume** and **LinkedIn Profile Content**

# Feed Forward
1. A set of **job search titles** or job roles (~5)
  - answers "what are you, and what do you want to be?"
2. A set of **job search keywords** (~7)
  - answers "what do you do"
3. Job-Seeker Vault
  - sqlite? postgres? json? jsonb? UX editable?

Titles and keywords carry the entire user-facing exchange because they
are **the standard vocabulary the user shares with the market.** That is 
why the set is mutable and, hence, "close enough" is the bar.

## Out of Scope

Give the user a small number of cached JDs in their desired titles / roles 
to help with the "do they like this type of job" categorization and refinement.
Will this be need for cost-capping, or to keep new users engaged in the tool?

For now we'll just move to Phase 1 and search ~25 jobs as a batch. We might need
that many to get a realistic meta analysis... but will users do the manual labor?

---

# Phase 1: Find JDs (Likely a pay tier)

## Input

**Option 1** (manual scrape - works now)
- Use the search strings and job titles (from phase 0) in the job boards of your
choice (LinkedIn, Indeed, WTTJ).
- Filter out absolute garbage yourself (e.g. in LinkedIn, x out recruiters, salary lowballs, etc)
- Paste potential JDs into the "Apply/Maybe/No" comparison tool (LLM)

**Option 2** (common crawl and REGEX analysis - in design)
- pull or pull and cache from Common Crawl
- start with URL regex for (greenhouse, ashby, and lever) -> pull out company slugs
- hit the actual APIs or Common Crawl again for each company to grab open roles
- regex against title (uses roles and keywords from phase 0)
- optional human checkpoint here (user can say "always ask me", or "always submit up to CAP_PER_DAY")
- send potential JDs to the "should I apply" comparison tool (LLM) job seeker "vault" built in Phase 0

## Explore

Use the apply/maybe/no recommendations and the through-batch meta analysis to improve
actual skills (e.g. get a Kubernetes certificate) or to know what to beef up your Vault
/ Resume with. Currently user takes these actions on their own. Later: implement iterative
conversation option. The goal is that users can enter or be recommended 25 JDs and get at
least 3 "Apply" recommendations (5 is better) from each session batch, leading to significant
value felt in goal of applying to 10 "apply-recommended" jobs per week.

## Deliver

**Apply/maybe/no recommendation** for each JD plus meta analysis recommendations for 
the batch of JDs in the search session.

## Feed-Forward

1. "Apply" set of JDs (ideally 3+) + LLM analysis for each JD role and company
2. Tracked metadata (funnel analysis / dashboard)
  - search session tags
  - comparison results
  - meta analysis recommendations
3. (optionally) Improved Vault/Resume manually or through the conversational iteration 
process

## Out of Scope

requested: ability to reload the JD into the input boxes and re-edit them
requested: ability to edit/override the decision so user can send what they
want to the Tailoring phase

---

# Phase 2: Per-JD Resume Tailoring

basic features already implemented


needs improvement:
  - prompt is old, doesn't do as good a job as Nicole's personal Claude chat
  - add a place to add additional JD info (now that the user is looking at 
the company and the JD more closely themselves)
  - add cover letter generation
  - add a place to input application questions
  - formatting options
  - formatting recommendations

---

# Phase 3: Tracking Dashboard (not implemented)

## Input
- log when you got interviews or when you got rejected

# Deliver
- prep help
- thank you note reminders
- async generation of these things
- interview reminders
- funnel analysis
- graph
- recommendations for best search strings / job boards / role titles for you

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

## 7. Tweaks and Deeps component contracts

2 reusable components for LLM iteration. These work off the Vault data, not "Resumes."
This is initial design thoughts. Probably need to get the vault schema done first.

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

**YOU BETTER BE LOGGING THIS!!!**
The feedback lane logs **which** of the three responses fired, not just accept or
reject. "Use this exact instead:" is the user overriding the model in their own
words. That is the highest-value signal in the product.

These two widgets are how the no-direct-chat constraint holds. Every turn is a
schema'd exchange I control, and it still reads as conversation to the user.

---

## 9. Deferred

**Fingerprinting.** "99% of general counsels have this bullet and you don't." A hard
statistic instead of a model's opinion, and the credibility argument against "just
use ChatGPT." It needs scale, so it waits. The bucket decomposition in Sprint 0 could
be its prerequisite.

**SOC / O\*NET as a durable key.** Free-text titles have forty spellings and
fingerprinting needs one. Not needed for the regex filter - need human eyes on
this before we decide how to use it.

**Seniority as a scoring input.** Rejected as a filter. A model reading a JD
body can judge whether the scope matches someone's history, and that is a judgment
rather than a string match. If it returns, it returns in the JD-scoring path, not
in intake.

**The funnel visual.** All open jobs, narrowing down to our funnel, then the 
interview funnel beyond.

