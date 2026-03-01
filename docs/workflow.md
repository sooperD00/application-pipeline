# The Workflow

This documents the manual job search workflow that ApplicationPipeline automates. It was developed over months of real job searching and refined through hundreds of applications. It's the "why" behind every feature.

## The Problem

Modern job boards return hundreds of results. Most are noise. The signal-to-noise ratio is terrible, and the cost of applying to a bad-fit job is high: time spent tailoring materials, emotional energy, and diluted focus.

The real bottleneck isn't finding jobs — it's *deciding which ones deserve your time* and *doing the repetitive tailoring work* for the ones that do.

## The Funnel

Every stage is a filter. Each one cuts volume and increases signal.

```
Stage 0: Scrape       600 results → 25 JDs       (~2 min)
Stage 1: Analyze      25 JDs → 4-6 Apply          (~5 min, AI-assisted)
Stage 2: Enrich       Apply set → tracked, linked  (~5 min per JD)
Stage 3: Tailor       Apply set → resumes, CLs     (~10 min, AI background)
Stage 4: Apply        Submit applications           (manual, per application site)
Stage 5: Interview    Prep docs, thank-you notes    (AI-assisted, on demand)
```

Total time from "open LinkedIn" to "6 applications generating in background": **~20 minutes**.

## Stage 0: Scrape

**What you do**: Open a job board. Set filters (remote, posted in last 24 hours, job category). Use a search term from your rotation list (e.g., "staff data engineer", "senior backend engineer", "platform engineer").

**What you capture**: Copy-paste each JD's text into the platform, one at a time. The platform auto-cleans the text (strips empty lines, normalizes whitespace, removes non-printable characters). You note metadata once per session: which board, which filters, which search term.

**The constraint**: Each session uses one metadata set. This keeps analytics clean — you can later see which search terms and boards produce the most callbacks.

**The skill**: Quickly X-ing out obvious mismatches before pasting. Low salary, crypto, hourly wage, companies you've researched and rejected. This is fast pattern recognition that's hard to automate and not worth automating — the human eye-scan takes seconds per result.

**Volume**: ~25 JDs per session (one page of LinkedIn results, minus the obvious rejects).

## Stage 1: Analyze

**What the AI does**: Examines each JD against your resume(s). For each JD:
- Breaks out requirements as met / partially met / not met
- Assesses overall fit level
- Recommends Apply / Maybe / No

The AI sees all 25 JDs in one conversation (sent in batches of 5 for context management). This is important — it enables cross-JD observations like "your strongest differentiator across these roles is X" or "this search term is producing low-fit results, try Y instead."

**What you do**: Watch the cards sort themselves. Review the Apply set. Override if you disagree. Move to enrichment.

**The insight**: Since adopting AI-assisted analysis, callback rates increased. The AI catches fit signals humans skip when skimming, and — more importantly — it catches *mis*-fit signals that would waste application effort.

## Stage 2: Enrich

**What you do for each Apply JD**:
1. Go back to the job board and grab the application link
2. Browse the application — note required questions, their types (yes/no, short answer, long answer, PDF upload), and whether a cover letter is needed
3. Copy-paste any additional JD text from the application site (sometimes differs from the board listing)
4. Note compensation information if visible
5. Add all of this to the tracking system

**The conditional gate** (~10% of cases): Sometimes application questions reveal dealbreakers, or you find the same company posted multiple similar roles. The platform supports flagging these for a separate AI conversation to decide whether to proceed.

**Why this matters**: Application questions are signal. They tell you what the hiring manager considers important. A role that asks "describe your experience with distributed systems at scale" is a different conversation than one that asks "are you authorized to work in the US? (y/n)."

## Stage 3: Tailor

**What the AI does** (in parallel, in the background):
- Generates a tailored resume for each Apply JD
- Generates a cover letter if requested
- Drafts answers to application questions if provided
- Uses the specific resume version you selected and the full analysis context from Stage 1

**What you do**: Come back, review the outputs, make edits, export as docx. Submit applications.

**The key**: This runs in parallel. 4 tailoring jobs at once. You can leave the platform and come back to finished drafts.

## Stage 4-5: Apply and Interview

Application submission is manual (you're interacting with each company's portal). The platform tracks what you've submitted and when.

When you get an interview, the platform carries forward all context — the JD, the analysis, the tailored resume, the application questions — into an interview prep conversation. Each interview stage (phone screen, technical, behavioral, etc.) gets its own prep document and its own tracking entry.

## The Analytics Layer

Over time, the tracking data reveals patterns:
- Which search terms produce the most Apply recommendations?
- Which boards have the highest callback rate?
- Which resume version performs best for which role types?
- What's your conversion rate at each funnel stage?
- Are you hitting your weekly application targets?

This turns job searching from "spray and pray" into an optimizable process.

## Design Principles

1. **The human stays in the loop for judgment calls.** The AI analyzes; the human decides. Status overrides are always available.
2. **Parallel processing where possible.** Batch analysis, parallel tailoring, background generation. The user's time is the bottleneck, not compute.
3. **One session, one metadata set.** Keeps analytics clean and sessions focused.
4. **Persistence across sessions.** The tracker is the long-running record. Sessions are work units within it.
5. **Prompts are visible and editable.** The AI's instructions are not a black box. Power users can tune them. This is the content moat.
