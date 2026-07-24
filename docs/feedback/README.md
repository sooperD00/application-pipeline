# Feedback

Raw feedback lives in `notes/` — one file per sitting, named
`YYYY-MM-DD-source.md`. Notes are never edited after they're written.

Extraction runs live in `batches/`. Each batch names the notes it
consumed, so coverage is derivable: anything in `notes/` not named by
a file in `batches/` hasn't been processed yet.

To run a pass: hand `PROMPT.md` and the unprocessed notes to Claude.