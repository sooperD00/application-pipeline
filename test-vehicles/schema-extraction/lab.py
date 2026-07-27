"""
Runner. Reads samples/*.txt, decomposes each one, measures what survived,
writes out/*.json and out/report.html.

 # Dry Run
    python lab.py --dry-run --only example
    python lab.py --dry-run            # no API key needed, fake extraction,
                                       # exercises the report pipeline
# Real Money Will Be Spent    
    python lab.py                      # everything in samples/, cached
    python lab.py --only crawford      # one sample
    python lab.py --model claude-opus-4-8
    python lab.py --no-cache           # force fresh calls
    
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
import loaders
import prompt as prompt_mod
from schema import Extraction, SCHEMA_VERSION
import prompt as prompt_mod
import report as report_mod

load_dotenv()   # copies .env into os.environ; without this the key is invisible
ROOT = Path(__file__).parent
SAMPLES = ROOT / "samples"
OUT = ROOT / "out"
CACHE = OUT / ".cache"

DEFAULT_MODEL = "claude-opus-5"

# Structured outputs are also available on claude-sonnet-5 and
# claude-haiku-4-5-20251001. Worth running the same sample through two of them:
# if Haiku and Opus disagree about where a line goes, the ambiguity is in your
# schema, not in the model.


# ---------------------------------------------------------------------------
# input
# ---------------------------------------------------------------------------

def read_samples(only: str | None) -> list[tuple[str, str, str]]:
    """Returns (name, kind, text). Kind comes from an optional first line:
    `#kind: cv`  —  one of resume | cv | linkedin | freeform | other.
    Anything in ALLOWED_FILE_TYPES is fair game; loaders.py turns it into text."""
    out = []
    for p in sorted(SAMPLES.iterdir()):
        if p.is_dir() or p.suffix.lower() not in loaders.ALLOWED_FILE_TYPES:
            continue
        if only and only.lower() not in p.name.lower():
            continue

        try:
            raw, warnings = loaders.load(p)
        except loaders.LoadError as e:
            print(f"  -- skipping {p.name}: {e}", file=sys.stderr)
            continue
        for w in warnings:
            print(f"  !! {p.name}: {w}", file=sys.stderr)

        kind = "unknown"
        if raw.lstrip().lower().startswith("#kind:"):
            first, _, rest = raw.lstrip().partition("\n")
            kind = first.split(":", 1)[1].strip().lower()
            raw = rest
        out.append((p.stem, kind, raw.strip()))
    return out


# ---------------------------------------------------------------------------
# coverage: how much of the document survived decomposition
# ---------------------------------------------------------------------------

def _normalize(s: str) -> tuple[str, list[int]]:
    """Lowercase, collapse whitespace, and keep a map back to original offsets."""
    chars: list[str] = []
    idx: list[int] = []
    prev_space = True
    for i, ch in enumerate(s):
        if ch.isspace():
            if not prev_space:
                chars.append(" ")
                idx.append(i)
                prev_space = True
        else:
            chars.append(ch.lower())
            idx.append(i)
            prev_space = False
    return "".join(chars), idx


@dataclass
class Coverage:
    owner: list[int]           # per original char: bucket index, or -1
    fabricated: list[int] = field(default_factory=list)   # bucket indices whose quote isn't in the source
    covered_chars: int = 0
    total_chars: int = 0

    @property
    def pct(self) -> float:
        return 100.0 * self.covered_chars / self.total_chars if self.total_chars else 0.0


def measure(source: str, buckets) -> Coverage:
    norm, idx = _normalize(source)
    owner = [-1] * len(source)
    cov = Coverage(owner=owner)

    for b_i, b in enumerate(buckets):
        q = (b.source_quote or "").strip()
        if not q:
            continue
        qn, _ = _normalize(q)
        if not qn:
            continue

        at = norm.find(qn)
        span = len(qn)
        if at == -1:
            # anchor on the opening of the quote; models sometimes drift or
            # truncate at the tail, which is forgivable. A missing head is not.
            anchor = qn[:60]
            at = norm.find(anchor) if len(anchor) >= 20 else -1
            if at == -1:
                cov.fabricated.append(b_i)
                continue
            span = min(span, len(norm) - at)

        start = idx[at]
        end = idx[min(at + span, len(idx)) - 1] + 1
        for i in range(start, end):
            if owner[i] == -1:
                owner[i] = b_i

    cov.total_chars = sum(1 for c in source if not c.isspace())
    cov.covered_chars = sum(
        1 for i, c in enumerate(source) if not c.isspace() and owner[i] != -1
    )
    return cov


# ---------------------------------------------------------------------------
# extraction
# ---------------------------------------------------------------------------

def cache_path(model: str, kind: str, text: str) -> Path:
    key = prompt_mod.cache_key_material(model, kind, text)
    return CACHE / f"{hashlib.sha256(key.encode()).hexdigest()[:16]}.json"


def extract(name, kind, text, model, max_tokens, use_cache) -> tuple[Extraction, dict]:
    cp = cache_path(model, kind, text)
    if use_cache and cp.exists():
        blob = json.loads(cp.read_text())
        return Extraction.model_validate(blob["extraction"]), {**blob["meta"], "cached": True}

    import anthropic

    client = anthropic.Anthropic()   # reads ANTHROPIC_API_KEY
    system, user = prompt_mod.build(kind, text)

    resp = client.messages.parse(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
        output_format=Extraction,
    )

    if resp.stop_reason == "max_tokens":
        print(
            f"  !! {name}: hit max_tokens ({max_tokens}). The extraction is truncated "
            f"and the coverage number below is meaningless. Re-run with --max-tokens larger.",
            file=sys.stderr,
        )

    meta = {
        "model": model,
        "input_tokens": resp.usage.input_tokens,
        "output_tokens": resp.usage.output_tokens,
        "stop_reason": resp.stop_reason,
        "cached": False,
    }
    ex = resp.parsed_output

    CACHE.mkdir(parents=True, exist_ok=True)
    cp.write_text(json.dumps({"extraction": ex.model_dump(), "meta": meta}, indent=2))
    return ex, meta


def stub_extract(text: str) -> Extraction:
    """--dry-run: a deliberately mediocre extraction so the report pipeline can be
    exercised without spending anything. Note it leaves real gaps — that's the point,
    you want to see what an imperfect run looks like before you trust a good one."""
    from schema import Bucket

    lines = [l.strip() for l in text.splitlines() if len(l.strip()) > 25]
    buckets = []
    for i, line in enumerate(lines[:14]):
        t = ("accomplishment" if line.lstrip().startswith(("-", "•", "*"))
             else "narrative" if i == 0
             else "unclassified" if i % 7 == 6
             else "role")
        buckets.append(Bucket(
            type=t, title=line[:40], content=line, source_quote=line,
            org="Example Org" if t == "role" else "", start="", end="",
            parent_role_title="", hedge="", issuer="", identifier="",
            section_hint="Experience", confidence=0.6,
            note="dry-run stub; nothing was actually classified" if t == "unclassified" else "",
        ))
    return Extraction(
        doc_kind="other", overall_quality="medium",
        quality_reasoning="Dry run — no model was called.",
        suggested_titles=["(dry run)"], buckets=buckets, leftover="",
    )


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--max-tokens", type=int, default=16000)
    ap.add_argument("--no-cache", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    samples = read_samples(args.only)
    if not samples:
        print(f"No .txt files in {SAMPLES}/. Drop some in and re-run.")
        return 1
    if not args.dry_run and not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY isn't set. Either export it or use --dry-run.")
        return 1

    OUT.mkdir(exist_ok=True)
    results, tok_in, tok_out = [], 0, 0

    for name, kind, text in samples:
        print(f"→ {name} ({kind or 'unknown'}, {len(text):,} chars)")
        if args.dry_run:
            ex, meta = stub_extract(text), {"model": "dry-run", "cached": False,
                                            "input_tokens": 0, "output_tokens": 0}
        else:
            ex, meta = extract(name, kind, text, args.model,
                               args.max_tokens, not args.no_cache)
        tok_in += meta.get("input_tokens", 0)
        tok_out += meta.get("output_tokens", 0)

        cov = measure(text, ex.buckets)
        counts: dict[str, int] = {}
        for b in ex.buckets:
            counts[b.type] = counts.get(b.type, 0) + 1

        (OUT / f"{name}.json").write_text(
            json.dumps({"meta": meta, "coverage_pct": round(cov.pct, 1),
                        "extraction": ex.model_dump()}, indent=2)
        )
        results.append({"name": name, "kind": kind, "text": text,
                        "ex": ex, "cov": cov, "counts": counts, "meta": meta})

        flag = "  ← LOOK" if counts.get("unclassified") or cov.fabricated or cov.pct < 85 else ""
        print(f"   coverage {cov.pct:5.1f}%   buckets {len(ex.buckets):3d}   "
              f"unclassified {counts.get('unclassified', 0):2d}   "
              f"fabricated spans {len(cov.fabricated):2d}"
              f"{'  (cached)' if meta.get('cached') else ''}{flag}")

    report_mod.write(OUT / "report.html", results, args.model, SCHEMA_VERSION)
    print(f"\n{tok_in:,} in / {tok_out:,} out tokens this run (cached calls cost nothing).")
    print(f"Report: {OUT / 'report.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
