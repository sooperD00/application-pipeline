"""
The two human checkpoints, before anything is spent.

Phase 1 answers "did I grab the wrong files" from stat() alone — no file is
opened for content, so a 50 GB stray costs 125 microseconds to notice instead of
however long it takes to parse. Bail here and go fix samples/.

Phase 2 answers "will it truncate, what will it cost". By then extraction has
run, which is local and free. Bail here and nothing has hit the API.

Both are skipped under --dry-run (nothing to spend) and --yes (you already looked).
"""

from __future__ import annotations
from pathlib import Path

BIG_FILE_BYTES = 10 * 1024 * 1024   # "that is not a resume" territory
TRUNCATE_AT = 0.80                  # of max_tokens; output tracks the DOCUMENT

# Blended over prose and schema JSON, which tokenize at very different rates.
# Measured: 2.62 on the Opus 5 Profile.pdf run, 3.21 on Haiku 4.5. Models from
# 4.7 on use a newer, denser tokenizer; take the denser figure so the gate
# over-estimates rather than under-estimates. One rate splits into two (a prose
# slope and a fixed intercept) once ledger.csv has enough rows to regress.
CHARS_PER_TOKEN = 2.6


def est_tokens(chars: int) -> int:
    return round(chars / CHARS_PER_TOKEN)


def est_input(doc_chars: int, fixed: dict[str, int]) -> int:
    """One call's input: the document plus everything wrapped around it."""
    return est_tokens(doc_chars) + sum(est_tokens(v) for v in fixed.values())


# ---------------------------------------------------------------------------
# formatting
# ---------------------------------------------------------------------------

def human_size(n: int) -> str:
    if n == 0:
        return "0 B"
    for unit, cut in (("GB", 1 << 30), ("MB", 1 << 20), ("KB", 1 << 10)):
        if n >= cut:
            return f"{n / cut:.1f} {unit}"
    return f"{n} B"


def shorten(name: str, width: int = 34) -> str:
    """Middle-truncate, keep the extension. Keeps the size column aligned."""
    if len(name) <= width:
        return name
    stem, dot, ext = name.rpartition(".")
    keep = width - len(ext) - 2
    return f"{stem[:keep]}….{ext}" if dot else name[: width - 1] + "…"


def gate(prompt: str, auto_yes: bool) -> None:
    """Enter continues, Ctrl-C bails. Never fires when there's nothing at stake."""
    if auto_yes:
        return
    try:
        input(f"\n{prompt}   [Enter] continue   [Ctrl-C] bail  ")
    except (KeyboardInterrupt, EOFError):
        print("\nstopped.")
        raise SystemExit(1)


# ---------------------------------------------------------------------------
# phase 1 — what will it grab?  (stat only, nothing opened for content)
# ---------------------------------------------------------------------------

def phase1(sample_dir: Path, only: str | None, allowed: set[str],
           detect, auto_yes: bool) -> list[Path]:
    """Prints the inventory, gates, returns the paths to actually process."""
    keep: list[tuple[Path, int]] = []
    skip: list[tuple[str, str]] = []

    for p in sorted(sample_dir.iterdir()):
        if p.is_dir():
            continue
        if only and only.lower() not in p.name.lower():
            continue
        if p.suffix.lower() not in allowed:
            skip.append((p.name, f"unsupported type {p.suffix.lower() or '(none)'}"))
            continue
        keep.append((p, p.stat().st_size))

    if not keep and not skip:
        print(f"Nothing in {sample_dir}/ to run. Drop some files in.")
        return []

    keep.sort(key=lambda kv: kv[1], reverse=True)

    by_ext: dict[str, int] = {}
    for p, _ in keep:
        by_ext[p.suffix.lower()] = by_ext.get(p.suffix.lower(), 0) + 1
    tally = "    ".join(f"{e}  {n}" for e, n in sorted(by_ext.items()))

    print(f"\n{sample_dir.name}/ — {len(keep)} file{'s' * (len(keep) != 1)}"
          f"{f', {len(skip)} skipped' if skip else ''}")
    print(f"  {tally}\n")

    if skip:
        print(f"  ! {len(skip)} skipped")
        for name, why in skip:
            print(f"      {shorten(name):<36} {why}")
        print()

    flags: list[str] = []
    for p, size in keep:
        note = ""
        if size == 0:
            note = "  ← empty"
            flags.append(f"{p.name} is empty")
        elif size > BIG_FILE_BYTES:
            note = "  ← big"
            flags.append(f"{p.name} is {human_size(size)} — phase 2 will parse it")

        # 8 bytes off the front. Does not load the file.
        real = detect(p)
        liar = f"  (actually {real})" if real != p.suffix.lower() else ""
        print(f"  {shorten(p.name):<36} {human_size(size):>9}{liar}{note}")

    if flags:
        print()
        for f in flags:
            print(f"  ! {f}")

    gate("look right?", auto_yes)
    return [p for p, _ in keep]


# ---------------------------------------------------------------------------
# phase 2 — how big, will it truncate, what will it cost
# ---------------------------------------------------------------------------

def phase2(loaded, max_tokens: int, is_cached, auto_yes: bool,
           fixed: dict[str, int]) -> None:
    """`loaded` is a list of (name, kind, text, warnings). Extraction already ran."""
    ceiling = TRUNCATE_AT * max_tokens
    rows, warn_lines, fresh_doc_tok, n_cached = [], [], 0, 0

    for name, kind, text, warnings in loaded:
        est = est_tokens(len(text))
        cached = is_cached(kind, text)
        n_cached += cached
        if not cached:
            fresh_doc_tok += est
        rows.append((name, len(text), est, cached, est > ceiling))
        for w in warnings:
            warn_lines.append(f"      {shorten(name, 24):<26} {w}")

    rows.sort(key=lambda r: r[2], reverse=True)

    print(f"\nextracted {len(rows)} file{'s' * (len(rows) != 1)}\n")
    print(f"  {'name':<30} {'chars':>8} {'~doc_tok':>9}   cache")
    for name, chars, est, cached, over in rows:
        print(f"  {shorten(name, 30):<30} {chars:>8,} {est:>9,}   "
              f"{'CACHED' if cached else 'fresh ':<6}"
              f"{'  ← may truncate' if over else ''}")

    if warn_lines:
        print(f"\n  ! warnings")
        for line in warn_lines:
            print(line)

    n_over = sum(1 for r in rows if r[4])
    if n_over:
        print(f"\n  ! {n_over} file(s) may blow --max-tokens {max_tokens:,}. "
              f"Buckets quote verbatim, so output tracks the document.")
        print(f"    Coverage numbers from a truncated run are meaningless. "
              f"Re-run those with --max-tokens larger.")

    n_fresh = len(rows) - n_cached
    n_fresh = len(rows) - n_cached
    f = {k: n_fresh * est_tokens(v) for k, v in fixed.items()}
    fix_tok = sum(f.values())

    print(f"\n  {n_fresh} fresh / {n_cached} cached\n")
    print(f"  document + fixed (system + schema + template)")
    print(f"  {fresh_doc_tok:,} + {fix_tok:,} "
          f"({f['system']:,} + {f['schema']:,} + {f['template']:,})"
          f" = ~{fresh_doc_tok + fix_tok:,} input tokens to spend")
    print("")

    gate("spend it?", auto_yes)
