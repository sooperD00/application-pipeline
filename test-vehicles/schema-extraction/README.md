# schema-extraction (Vault Onboarding / Intake Lab)

A throwaway rig for one question: **do five bucket types cover a real career document?**

Nothing here is production code. It exists to be run twenty times against
different samples and different schemas until the shape stops moving, and then
thrown away.

## Run it

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

# 5. Run it
python lab.py --dry-run     # no key needed, fake extraction, proves the plumbing
python lab.py               # the real thing
open out/report.html
```

Drop files into `samples/`. One person per file, filename becomes the
label. Check ALLOWED_FILE_TYPES in loader.py, e.g.
```python
ALLOWED_FILE_TYPES = {".txt", ".md", ".pdf", ".docx"}
```
In `.txt` files, optional first line tells the model what it's looking at:

```
#kind: cv
```

`resume`, `cv`, `linkedin`, `freeform`, `other`. It's only a hint — if the
content disagrees, the model overrides it and the report shows what it decided.

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

## Things worth trying once it runs

- Same sample through `--model claude-haiku-4-5-20251001` and
  `--model claude-opus-4-8`. Where they disagree about placement, the ambiguity
  is in your schema, not in the model.
- Run the same sample twice with `--no-cache`. Anything that lands in a
  different bucket between identical runs is a prompt problem, not a schema
  problem.
- The real acceptance test, once the enum looks stable: take the buckets, throw
  the source text away, and feed just the buckets plus a live JD to your existing
  tailoring prompt. If the output holds up against what the blob path produces
  today, the model is right. You already have the control group.

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
```

Verified — same PDF under two names:

```text
Profile.pdf  -> 5bc54aacc0242031.json
RENAMED.pdf  -> 5bc54aacc0242031.json
same key: True
```