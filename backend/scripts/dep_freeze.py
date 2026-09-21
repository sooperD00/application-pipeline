"""Freeze-file utilities for the pip -> uv migration.

[SPRINT-a75ff1-c-CLEANUP] Scaffolding for the dependency sprint only: it exists to prove the
packaging move did not move versions. The upgrade leg is the last consumer -- it re-runs
`compare` once the constraints come out of pyproject.toml -- and deletes this at its close.

Two jobs, both pure enough to unit-test:

  constraints   read a `pip freeze` file, emit -- or write in place -- the
                [tool.uv] constraint-dependencies block in pyproject.toml
  compare       diff two freeze files by *normalized* package name, so that
                `Jinja2` and `jinja2` do not read as a change

This never contacts a registry and never chooses a version. Every number it emits came out
of a freeze file you generated on your own machine.

Usage (from backend/, old venv active for the baseline). The freeze files live in
test-vehicles/freezes/a75ff1-pip-to-uv/:

    F=../test-vehicles/freezes/a75ff1-pip-to-uv
    python scripts/dep_freeze.py constraints $F/baseline-freeze.txt --write pyproject.toml
    python scripts/dep_freeze.py compare $F/baseline-freeze.txt $F/uv-freeze.txt
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BEGIN = "# >>> BEGIN GENERATED CONSTRAINTS >>>"
END = "# <<< END GENERATED CONSTRAINTS <<<"

_SEPARATORS = "-_."


# ---------------------------------------------------------------- pure functions


def normalize_name(name: str) -> str:
    """PEP 503 normalization: case-folded, runs of - _ . collapsed to a single -."""
    out: list[str] = []
    previous_was_separator = False
    for char in name.strip():
        if char in _SEPARATORS:
            if not previous_was_separator:
                out.append("-")
            previous_was_separator = True
        else:
            out.append(char)
            previous_was_separator = False
    return "".join(out).lower()


def _pin_from(line: str) -> tuple[str, str] | None:
    """Return (normalized_name, version) for a `name==version` line, else None."""
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or stripped.startswith("-"):
        return None
    if "==" not in stripped:
        # editable installs, `name @ file:///...` direct references, bare names
        return None
    name, _, remainder = stripped.partition("==")
    version = remainder.split(";")[0].split("--")[0].split("#")[0].strip()
    if not version:
        return None
    return normalize_name(name), version


def parse_freeze(text: str) -> dict[str, str]:
    """Map normalized package name -> version for every pinned line."""
    pins: dict[str, str] = {}
    for line in text.splitlines():
        pin = _pin_from(line)
        if pin is not None:
            pins[pin[0]] = pin[1]
    return pins


def unparsed_lines(text: str) -> list[str]:
    """Non-empty, non-comment lines that carry no `==` pin.

    These are the lines a naive parser would drop silently -- editable installs, local
    file:// references. Surfaced so a package can never vanish from the comparison unseen.
    """
    leftovers: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if _pin_from(line) is None:
            leftovers.append(stripped)
    return leftovers


def render_constraints(pins: dict[str, str]) -> str:
    """The TOML array, sorted, ready to sit under [tool.uv]."""
    lines = ["constraint-dependencies = ["]
    for name in sorted(pins):
        lines.append(f'    "{name}=={pins[name]}",')
    lines.append("]")
    return "\n".join(lines)


def replace_block(toml_text: str, block: str) -> str:
    """Swap whatever sits between the sentinels for `block`. LF text in, LF text out."""
    lines = toml_text.split("\n")
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == BEGIN)
        stop = next(i for i, line in enumerate(lines) if line.strip() == END)
    except StopIteration:
        raise ValueError(
            f"sentinels not found -- pyproject.toml needs a {BEGIN} / {END} pair"
        ) from None
    if stop < start:
        raise ValueError("END sentinel appears before BEGIN sentinel")
    return "\n".join(lines[: start + 1] + block.split("\n") + lines[stop:])


def diff_pins(
    baseline: dict[str, str], candidate: dict[str, str]
) -> tuple[list[str], list[str], list[str]]:
    """(added, removed, changed) -- changed means same package, different version."""
    added = sorted(set(candidate) - set(baseline))
    removed = sorted(set(baseline) - set(candidate))
    changed = sorted(
        name
        for name in set(baseline) & set(candidate)
        if baseline[name] != candidate[name]
    )
    return added, removed, changed


# ---------------------------------------------------------------- file i/o


def read_preserving_newline(path: Path) -> tuple[str, str]:
    """Return (LF-normalized text, the newline the file actually uses)."""
    raw = path.read_bytes()
    newline = "\r\n" if b"\r\n" in raw else "\n"
    return raw.decode("utf-8").replace("\r\n", "\n"), newline


def write_with_newline(path: Path, text: str, newline: str) -> None:
    path.write_bytes(text.replace("\n", newline).encode("utf-8"))


# ---------------------------------------------------------------- commands


def cmd_constraints(args: argparse.Namespace) -> int:
    freeze_text = Path(args.freeze).read_text(encoding="utf-8")
    pins = parse_freeze(freeze_text)
    if not pins:
        print(f"no pinned packages found in {args.freeze}", file=sys.stderr)
        return 1

    for leftover in unparsed_lines(freeze_text):
        print(f"skipped (no == pin): {leftover}", file=sys.stderr)

    block = render_constraints(pins)

    if not args.write:
        print(block)
        print(f"\n{len(pins)} packages", file=sys.stderr)
        return 0

    target = Path(args.write)
    text, newline = read_preserving_newline(target)
    write_with_newline(target, replace_block(text, block), newline)
    print(f"wrote {len(pins)} constraints into {target}", file=sys.stderr)
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    baseline_text = Path(args.baseline).read_text(encoding="utf-8")
    candidate_text = Path(args.candidate).read_text(encoding="utf-8")
    baseline = parse_freeze(baseline_text)
    candidate = parse_freeze(candidate_text)

    for label, text in ((args.baseline, baseline_text), (args.candidate, candidate_text)):
        for leftover in unparsed_lines(text):
            print(f"skipped in {label} (no == pin): {leftover}", file=sys.stderr)

    added, removed, changed = diff_pins(baseline, candidate)

    print(f"baseline  {args.baseline}: {len(baseline)} packages")
    print(f"candidate {args.candidate}: {len(candidate)} packages")

    if not (added or removed or changed):
        print("\nIDENTICAL -- same packages, same versions")
        return 0

    for name in added:
        print(f"  + {name}=={candidate[name]}")
    for name in removed:
        print(f"  - {name}=={baseline[name]}")
    for name in changed:
        print(f"  ~ {name}: {baseline[name]} -> {candidate[name]}")
    print(f"\nDIFFERENT -- {len(added)} added, {len(removed)} removed, {len(changed)} changed")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p_constraints = sub.add_parser(
        "constraints", help="turn a pip freeze into a constraint-dependencies block"
    )
    p_constraints.add_argument("freeze", help="path to a pip freeze output file")
    p_constraints.add_argument(
        "--write",
        metavar="PYPROJECT",
        help="write the block into this pyproject.toml between the sentinels",
    )
    p_constraints.set_defaults(func=cmd_constraints)

    p_compare = sub.add_parser("compare", help="diff two freeze files by normalized name")
    p_compare.add_argument("baseline")
    p_compare.add_argument("candidate")
    p_compare.set_defaults(func=cmd_compare)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
