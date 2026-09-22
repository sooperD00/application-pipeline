# Scrubbing personal data

**ID**: `[s-572aff]`
**Status**: planned
**Phase**: 1

Take other people's personal data out of the public repo, and build the path that keeps the next
batch of scraped material from carrying more of it in.
**Entry gate:** none.
**Legs:** redact what is already out (bugfix), then build the scrub path (feature). One is a
sweep of what exists; the other is tooling for what arrives next.

**Why now** Seven names and email addresses, one of them a work address, have been public since
`936ed83` on 2026-07-24 — the email itself went out on 2026-03-15, but the file landed here in
July. They are somebody else's to lose, which is what makes this urgent rather than tidy.
(Pulled from Housekeeping, 2026-09-22.)

The second half has a slower clock. The schema-extraction lab needs real scraped material to be
worth running, and the scrub path should exist before any of it is tracked rather than after.

## leg a — redact what is already public (bugfix) --- planned

**Kind:** bugfix — reproduce, fix, confirm. The sweep reproduces, the redaction fixes, and the
sweep run again is the regression test.

**Done when**
- [ ] the recipient block in `test-vehicles/feedback/asks/2026-03-15-beta-invite.md` is redacted.
      The front matter already records "7", so the file loses nothing
- [ ] the sweep covers every tracked file, not only the one already known: email addresses,
      phone numbers, street addresses, and anything else identifying a person who is not me.
      Each hit is either redacted or written down here as deliberate
- [ ] the sweep is a command someone else can run, written down in this file
- [ ] the sharing on the Google Doc linked from `test-vehicles/design/2026-07-20-greg-rowsey.md`
      is settled with Greg. A link in a public repo is public if the document is
- [ ] the history question is answered in writing, here: whether `936ed83` and anything else the
      sweep finds gets rewritten, and why
- [ ] whether the seven are told, answered in a line

**Watch** Redacting a file stops the next reader, not the ones who already cloned or crawled it.
A rewrite costs every clone and every fork, and GitHub serves unreachable objects by SHA for a
while after one. Decide it as harm reduction, not as deletion.

## leg b — a scrub path for scraped material (feature) --- planned

**Kind:** feature — import graph: the folder, then the script, then the first file through it.

The lab cannot hold real scraped input in the open, and it is not worth much without it. Raw
material lands somewhere gitignored, a script and its prompt replace what identifies a person
with plausible fakes, and only the cleaned copy is tracked.

**Done when**
- [ ] raw input has a gitignored home under `test-vehicles/schema-extraction/`, and
      `python3 scripts/check_docker_context.py` still exits 0 with files sitting in it
- [ ] the script and the prompt that drives it live in the lab, and one real file through them
      produces a cleaned copy whose fakes are consistent — the same person is the same fake
      person throughout the file
- [ ] a person reads one cleaned file end to end before any cleaned file is tracked. The script
      proposes; a human signs off
- [ ] the cleaned copies are tracked and the raw ones are not, confirmed with `git status`

**Watch** That lab's `.gitignore` has already swallowed a file it did not mean to: `ledger*.*`
took `ledger.py` with it, which is [h-9bbbc0]. Write the new rule narrowly, and check what it
matches before trusting it.
