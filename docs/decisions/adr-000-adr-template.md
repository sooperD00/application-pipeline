# ADR-NNN: Title in Title Case, a Noun Phrase

<!-- HOW TO USE THIS FILE
Copy it to adr-<NNN>-<short-name>.md, where NNN is the next free number in README.md. Numbers are
identity: never reuse one, never renumber, and if a number is spoken for before it is written,
say so in README.md rather than taking it. Add your row to the table there when you save.
Delete every comment as you fill it in. Delete any section that has nothing to say.

Write one when a choice will otherwise be re-litigated, when it constrains code that is not
written yet, or when it sets a convention — the convention then lives in the record, because a
rule kept somewhere else is a rule nobody can find. Do not write one to explain how code works;
that is a docstring or a comment next to the code.
-->

**Date**: YYYY-MM-DD
<!-- When the decision was made, not when it was typed. Recording it late is fine and worth
saying: 2026-08-30 (recorded 2026-09-17, after the first leg landed). -->

**Status**: Proposed | Accepted | Superseded by ADR-NNN
<!-- Add whatever qualifier makes it useful at a glance:
"Accepted — [s-9cf8b9-a] shipped 2026-09-16; [s-9cf8b9-b] and [s-9cf8b9-c] planned". -->

**Decision**: <!-- Two or three sentences, present tense, specific enough to act on. A reader who
stops here should still do the right thing. -->

**Why**: <!-- Three to five bullets, one line each. The reasons it was decided, not the story of
deciding it. Cut anything a reader already knows — nobody needs to be told that renumbering is
tedious or that big files are hard to read. -->
-
-

## One Section per Thing the Reader Has to Do

<!-- Instructions, not narrative. One bullet per action, each starting with a verb:

- Generate an ID with `openssl rand -hex 3`.
- Name the file `sprint-<id>-<short-name>.md` and put it in `remaining/`.
- Move it with `git mv` when it closes, never a copy-paste.

A rule reads best as a pair of lists, because the counter-examples are what people get wrong:

- Yes: `[s-9cf8b9]`, `[s-9cf8b9-c]`
- Never: `Sprint 19`, `19c`, a bare number

Reach for a table when the thing is a set of short definitions or a lookup — a glossary, or a
column per field. Reach for a fenced block when the thing is a directory layout, a command, or
a file format. Prose is the last resort, and a paragraph that says why is usually a bullet in
Why that escaped. -->

**Consequences**: <!-- What this costs: what gets harder, what now has to be maintained, what
breaks if the one file everything points at goes stale. The upside is already in Why, so this
section is the honest half. -->
-

**Alternatives considered**: <!-- One line each, three at most: what it was, and why not. An
option nobody can reconstruct comes back every six months and gets argued again. -->
-

<!-- **Update YYYY-MM-DD** — append one of these when the decision changes, gets qualified, or
gets overtaken. Never rewrite what the record said before; the point is that it can be read in
the order it was learned.
The exception is a record that works as a process handbook, like ADR-021: sessions follow it as
instructions, so it is edited in place to say the current rule, and git carries its history. -->
