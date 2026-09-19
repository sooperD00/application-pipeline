# ADR-013: Two-Layer Prompt Architecture — Public Templates vs. Private System Prompts

**Date**: 2026-03-07
**Status**: Proposed (deferred past MVP)

**Decision**: The prompt system has two layers that serve different purposes and have different visibility rules:

1. **PromptTemplate rows** (DB, `prompt_templates` table) — user-facing. These are the editable templates the UI exposes: analysis, resume_generation, cover_letter, app_answers. Users can read, fork, and version them. System defaults ship via the seed script. This is the product surface.

2. **`prompts/` directory** (files on disk, gitignored or kept private) — operator-facing. These are the *real* system prompts and meta-instructions: how the platform talks to Claude under the hood, what structured JSON schema to return, how to reason about fit assessment, what tone to use. The stuff that makes the output quality good. Users never see these; they're loaded at startup or embedded in the service layer.

The distinction matters because the repo is public. The PromptTemplate content is the "what" — users customize it and that's the product. The system prompts are the "how" — the prompt engineering that makes Claude's output worth paying for. Publishing the system prompts in a public repo hands competitors the most valuable part of the codebase for free.

**Current state**: System prompts are hardcoded as string constants in `services/analysis.py` and `services/tailoring.py`. This works but means they're visible in the public repo today. The `prompts/` directory in the README tree is a placeholder for extracting them to files that can be gitignored or loaded from a private source.

**When to implement**: Before the LinkedIn blog post / public launch. Not needed for MVP (Nicole is the only user and the repo has no traffic yet).

**Alternatives considered**: 
- Keep everything in the DB (simpler, but then system prompts are editable by users, which defeats the purpose — or you need a visibility flag and access control).
- Environment variables for system prompts (awkward for multi-paragraph text).
- Private git submodule (clean separation, but adds deployment complexity).
- Accept the risk (the workflow design and UX are the real moat, not the prompts). Possibly true, but no reason to give it away before testing that hypothesis.

**Update 2026-09-17** — still Proposed, now deferred to Phase 2+. Three things changed since this was written:

1. "Nicole is the only user" stopped being true on 2026-03-15, when beta invites went out to seven people. The repo still has no traffic to speak of, which is the part that actually gates this.
2. Both system prompts have been in the public git history since March — `ANALYSIS_SYSTEM_PROMPT` since 2026-03-04, `TAILORING_SYSTEM_PROMPT` since 2026-03-05. Extraction therefore protects the *next* version of a prompt, not the one shipping today. That is still worth doing, but it is a weaker claim than this ADR made when nothing had been published yet.
3. Two questions have to be answered before any extraction, and neither was visible in March:
   - **Where the files live.** The README tree says `backend/app/prompts/`; `sync-prompts.sh` expects a root `prompts/`. Either way, `.gitignore` and `.dockerignore` both exclude `prompts` at any depth, so files placed in either location reach neither GitHub nor a Docker build.
   - **How they reach production.** Railway builds from the GitHub snapshot, where git-ignored files never exist. "Loaded at startup" therefore needs a route in that does not depend on the file being in the repo — the env-var and private-submodule options above are the two candidates, and the env-var objection ("awkward for multi-paragraph text") is now the cheaper of the two problems.

Also worth recording: the in-code TODO in `analysis.py` points the opposite way, proposing to move the analysis system prompt *into* the user-editable PromptTemplate table. That is a different architecture from this one, not a step toward it. Pick one before either gets half-built. The work item is T-12 in remaining-sprints.md.
