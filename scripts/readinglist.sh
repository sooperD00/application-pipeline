#!/usr/bin/env bash
# readinglist.sh -- draft a sprint reading list from what the plan already says.
#
# NOT PORTED YET. Written for another project: it slices one big plan document and reads a
# DECISIONS.md of D-rows. This repo has a file per sprint and a folder of ADRs, so the paths
# and IDs below do not resolve here. Porting it is an item in the developer tooling sprint.
#
#   ./readinglist.sh 2C 3        # from "## Sprint 2C" up to "## Sprint 3"
#
# This produces a DRAFT. It found 9 of the 11 decisions Sprint 2C actually
# needs, missed 2, and volunteered 2 that should be skipped. Read the
# "WHAT THIS CANNOT SEE" block at the bottom of its own output before
# pasting anything into a prompt.
#
# Git Bash on Windows: uses only grep -E, sed, awk, sort, comm. No -P, no gawk
# extensions, no process substitution.

set -u
FROM="${1:-2C}"
TO="${2:-3}"
PLAN=docs/remaining-sprints.md
DEC=docs/DECISIONS.md
DID='D-[0-9]+[a-z]?'          # the [a-z]? matters: D-04a exists, and D-[0-9]+ eats "D-04" out of it


# Slice the sprint
sprint () {
  awk -v a="^## Sprint $FROM" -v b="^## Sprint $TO" '$0~b{f=0} $0~a{f=1} f' "$PLAN"
}

TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

# -------------------------------------- 1. the seed (what the section names outright)
sprint | grep -oE "\b$DID\b"                          > "$TMP/seed"
sprint | grep -oE '\bT[1-8]\b'      | sort -u          > "$TMP/tests"
sprint | grep -oE '\bR[0-9]+\b'     | sort -u          > "$TMP/risks"
sprint | grep -oE '\bC[0-9]+\b'     | sort -u          > "$TMP/chglog"

# ------------------------------------------- 2. reverse edge: D-rows naming my tests
# some things are invisible going forward and obvious going backwards
: > "$TMP/rev"
while read -r t; do
  [ -n "$t" ] || continue
  grep -E "^\| $DID \|.*\b$t\b" "$DEC" | sed -E "s/^\| ($DID) \|.*/\1/" >> "$TMP/rev"
done < "$TMP/tests"

# ------------------------------------ 3. section 6's own test rows cite decisions
while read -r t; do
  [ -n "$t" ] || continue
  awk '/^## 6\. Tests/,/^## 7\./' "$DEC" \
    | grep -E "^\| $t " | grep -oE "\b$DID\b"          >> "$TMP/rev"
done < "$TMP/tests"

cat "$TMP/seed" "$TMP/rev" | sort -u                   > "$TMP/decisions"

# --------------------------------------------- 4. map each decision to its anchor
# Anchors, so the list names sections instead of IDs
IDS=$(tr '\n' '|' < "$TMP/decisions" | sed 's/|$//')
awk -v ids="$IDS" '
  /^## [0-9]/ {h=$0} /^### / {h=$0}
  /^\| D-[0-9]+[a-z]? \|/ {
    split($0, a, "|"); gsub(/^ +| +$/, "", a[2])
    if (a[2] ~ "^(" ids ")$") print a[2] "\t" h
  }' "$DEC" | sort -u                                  > "$TMP/anchors"

# decisions with no table row of their own -- they live only in a subsection
cut -f1 "$TMP/anchors" | sort -u                        > "$TMP/anchored"
comm -23 "$TMP/decisions" "$TMP/anchored"               > "$TMP/orphans"

# -------------------------------------------------- 5. the complement: DO NOT READ
{ echo "$PLAN"; echo "$DEC"; echo docs/ENGINE.md; echo engine.py; echo tax.py
  echo tests/test_engine.py; } | sort                  > "$TMP/onlist"
ls docs/*.md docs/review/*.md docs/sprints/*.txt *.py tests/*.py scripts/*.py 2>/dev/null \
  | sort | comm -23 - "$TMP/onlist"                    > "$TMP/skip"

# ----------------------------------------------------------------- 6. print it
echo "# DRAFT reading list -- Sprint $FROM.  VERIFY BEFORE USE."
echo
echo "READ IN FULL -- a DEFAULT, and the sprint's seam overrides it. See note 6."
echo "  engine.py, tax.py, tests/test_engine.py, docs/ENGINE.md"
echo "  functions this sprint names: $(sprint | grep -oE '\b[a-z_]+\(\)' | sort -u | tr '\n' ' ')"
echo
echo "docs/remaining-sprints.md"
echo "  - everything above '## Sprint 1'"
echo "  - '## Sprint $FROM' through the rule before '## Sprint $TO'"
echo "  - '## Tech Debt' and '## Housekeeping'"
echo
echo "docs/DECISIONS.md -- sections that contain the $(wc -l < "$TMP/decisions" | tr -d ' ') decisions below"
sed 's/^/  /' "$TMP/anchors" | sort -k2
while read -r d; do
  [ -n "$d" ] || continue
  echo "  $d	no table row -- look for '### $d' or a subsection"
done < "$TMP/orphans"
echo "  - '## 0. Precedence', '## 2. Definition of done', '## 5. Contracts', '## 6. Tests'"
[ -s "$TMP/tests" ]  && echo "  - '## 6. Tests', rows: $(tr '\n' ' ' < "$TMP/tests")"
[ -s "$TMP/risks" ]  && echo "  - '## 9. Open risks', rows: $(tr '\n' ' ' < "$TMP/risks")"
[ -s "$TMP/chglog" ] && echo "  - Gate 2 changelog, rows: $(tr '\n' ' ' < "$TMP/chglog")"
echo
echo "DO NOT READ"
sed 's/^/  /' "$TMP/skip"
echo
cat <<'EOF'
WHAT THIS CANNOT SEE -- check these by hand every time

  1. SEMANTIC dependencies. A decision you need but never cite is invisible.
     Sprint 2C needs D-21 (t_now is a deferral rate) because T5 compares the
     marker against it. Nothing anywhere writes "D-21" near Sprint 2C.

  2. Decisions named by PHRASE instead of by ID. 2C's done-when says the
     threshold "moves right, not left" -- that is D-40, by its own words.
     Recover these with a phrase pass:
     # Verify every anchor resolves before it goes in a prompt
        grep -oiE "^\| (D-[0-9]+|C[0-9]+) \|.*<phrase from the done-when>" docs/DECISIONS.md

  3. What to SKIP. Citation means relevance, never sufficiency and never
     necessity. This script hands you D-15 and D-39 for Sprint 2C; D-39's
     subsection is the longest in the file and 2C does not need it, because
     the half of T2 that depended on it closed in 2B.

  4. Its own two bugs, now fixed, as a warning about the class. D-[0-9]+ ate
     "D-04" out of D-04a; and pulling decisions from every row of section 6
     rather than only this sprint's tests dragged in D-16, which belongs to
     Sprint 3's rungs. Both looked like plausible output.

  5. UNDECIDED parameters. The reason to read a sprint's decisions by hand is
     to find what is not in them. 2C's bisection bracket and convergence
     tolerance are specified nowhere in this corpus, and no grep can return
     the absence of a thing.

  6. SEAMS -- which files this sprint must NOT open. The READ IN FULL block
     above is hardcoded and knows nothing about them, and it is the only block
     in this output asserted flat rather than labelled a draft, so a wrong line
     there reads as an instruction rather than as a guess. Check it by hand
     against the sprint's own seam paragraph before pasting.
        Sprint 4A  forbidden: tests/test_engine.py -- 2,601 lines, and the
                   largest thing this script would otherwise hand you
        Sprint 4B  forbidden: engine.py, spike_grid.py
        Sprint 6   forbidden: tests/test_engine.py (writes no tests),
                   spike_grid.py except one leftover cleanup tag
     Not recoverable by grep, for the same reason item 1 is not: the plan
     states the seam in prose, a section away from the file names.
     THIS ITEM HAS NOW FIRED FOUR TIMES AND ALWAYS ON THE SAME FILE.
     tests/test_engine.py is the largest thing this script can hand you and
     it has been forbidden in three of the last four sprints. Consider
     inverting the default: name it only when a sprint SAYS it writes tests.

  7. A SPRINT THAT DELETES A FILE. Sprint 6 replaces app.py wholesale, so
     app.py is required reading -- and this script put it under DO NOT READ,
     because nothing in the plan CITES a file the sprint is removing. The
     probe also carries six container facts (sys.path, --no-install-project,
     the PORT bind) that the replacing sprint would otherwise rediscover.
     Rule: if a sprint goal says it REPLACES or DELETES a file, read that
     file.

  8. A SPRINT WHOSE SPEC IS A PICTURE. Sprint 6 is the UI sprint and this
     script put docs/DESIGN.md under DO NOT READ. Part 3 is five captioned
     mockups and is the only place the interface exists visually; section 7
     is the contract but it is not the drawing. Nothing greps as a citation
     because the reference is an image link.
EOF
