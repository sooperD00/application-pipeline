Read every file in `batches/` first to see which notes have already
been processed and which items have already been extracted.

Then read the note files I've given you and extract actionable items.
Skip anything already captured in a previous batch.

For each item, output:
- **Title** — issue-ready, imperative, under 10 words
- **Category** — [FILL IN AFTER FIRST RUN]
- **Source** — note filename and who said it
- **Body** — what they hit, why it matters, what "done" looks like
- **Stale?** — flag if the note's `against:` tag predates a release
  that may have already fixed it
- **→ #___** — left blank for me to fill in with the issue number

Then write the whole thing to `batches/YYYY-MM-DD-batch-NN.md`,
opening with the list of note files consumed.

If this is the first run, don't use fixed categories — propose 4–6
based on what's actually in the notes, and explain each in one line.