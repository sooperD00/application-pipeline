# ADR-011: Dumb Renderer — Prompt Controls Formatting, Code Executes It

**Date**: 2026-03-05
**Status**: Accepted

**Decision**: The docx generation pipeline separates formatting *decisions* from formatting *execution*. Claude makes all formatting decisions (font sizes, bold/italic ranges, spacing, element ordering) guided by the `resume_generation` prompt template. Claude returns structured JSON describing the document element-by-element. `docx_builder.py` is a "dumb renderer" — it walks the JSON array and translates each element into python-docx calls without making any formatting choices of its own.

**Rationale**: The current manual workflow already works this way: a prompt tells Claude what formatting rules to follow, and Claude produces a docx with nuanced, per-JD formatting decisions (orphan bullet management, bold emphasis storytelling, whitespace calibrated to audience). Hardcoding formatting rules into Python would:

1. **Lose per-JD adaptability.** Claude currently adjusts formatting based on content length, audience, and emphasis needs. A rigid template can't do this.
2. **Lock formatting behind code changes.** Users (including future users with different preferences) would need a developer to change their resume style. With prompt-driven formatting, they edit a text template in the UI.
3. **Block the Phase N resume uploader.** The planned workflow is: user uploads a docx → system parses formatting into a prompt template → Claude uses that template for future tailoring. This requires formatting to live in prompt-space, not code-space.

The JSON schema is the contract between Claude and the renderer. It's expressive enough for Claude to communicate fine-grained decisions (per-element font sizes, specific bold substrings, hyperlink placement) while being simple enough for the renderer to stay truly dumb.

**The test**: If a user changes their prompt to say "use 12pt for everything and never bold anything," the system should honor it without a code change. With this architecture, it does.

**What the renderer hardcodes** (document-level, not content-level): page size (US Letter), margins, default font family (Calibri). These become configurable in a future sprint via a document-settings template.

**Alternatives considered**: 
- python-docx template with formatting hardcoded in Python (fast to build, but violates all three points above — formatting decisions would be split between prompt and code with no clear ownership).
- Claude returns raw docx bytes directly (not feasible — the API returns text, not binary files).
- Claude returns markdown, Python converts to docx (loses fine-grained formatting control; markdown can't express per-element font sizes or bold substrings).
