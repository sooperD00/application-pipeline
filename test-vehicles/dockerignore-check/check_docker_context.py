#!/usr/bin/env python3
"""Would Docker get any file that git ignores?

Asks git which files it ignores, asks Docker which files it would send as build context, and
prints the overlap. Neither ignore file is parsed here. Each tool answers for itself, so the
syntax differences between .gitignore and .dockerignore can't fool the check.

  python3 test-vehicles/dockerignore-check/check_docker_context.py           files on disk now
  python3 test-vehicles/dockerignore-check/check_docker_context.py --probe   a fake file for every
      ignore rule, in every folder the rule applies to, so gaps show up before a real file hits them

Run it from anywhere inside the repo. Docker must be running. It never changes your files, but
each run leaves a build-cache entry the size of the context (`docker builder prune` clears them).
Exit status: 0 nothing leaks, 1 leaks found, 2 couldn't check.

How it answers
  git ignores   git ls-files --others --ignored --exclude-standard
                (every .gitignore, .git/info/exclude, and your global excludes file)
  Docker gets   a throwaway build, FROM scratch + COPY . /, exported to a temp folder. Docker
                applies .dockerignore to it just like a real build, so the folder holds
                exactly what a real build would receive.
  which rule    git check-ignore --verbose
  where to      the Dockerfile's COPY lines. This is a simple parse, so treat it as a hint.
"""
import argparse
import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import namedtuple
from pathlib import Path

SHOW = 5  # leaked paths listed per rule before "... and N more"

Copy = namedtuple("Copy", "line stage final sources text")


class CantCheck(Exception):
    pass


def run(cmd, cwd=None, input=None, ok=(0,)):
    r = subprocess.run(cmd, cwd=cwd, input=input, capture_output=True, text=True)
    if r.returncode not in ok:
        raise CantCheck(f"`{' '.join(cmd)}` failed:\n{r.stderr.strip()}")
    return r.stdout


def git(cwd, *args, **kw):
    return run(["git", *args], cwd=cwd, **kw)


def nul_split(text):
    return [p for p in text.split("\0") if p]


def ancestors(path):
    parts = path.split("/")[:-1]
    return ["/".join(parts[:k]) for k in range(1, len(parts) + 1)]


def short(path):
    home = str(Path.home())
    return "~" + path[len(home):] if path.startswith(home) else path


# ---------------------------------------------------------------- the two answers

def git_ignores(repo):
    """Untracked files git ignores. -z keeps unusual file names from being quoted."""
    return set(nul_split(git(repo, "ls-files", "--others", "--ignored", "--exclude-standard", "-z")))


def docker_gets(context):
    """Files Docker would send as build context."""
    with tempfile.TemporaryDirectory(prefix="docker-context-") as out:
        run(["docker", "buildx", "build", "--progress=quiet", "--file", "-",
             "--output", f"type=local,dest={out}", str(context)],
            input="FROM scratch\nCOPY . /\n")
        return {p.relative_to(out).as_posix() for p in Path(out).rglob("*") if not p.is_dir()}


def blame(repo, paths):
    """{path: (rule file, line, pattern)} for the rule that makes git ignore each path."""
    if not paths:
        return {}
    f = git(repo, "check-ignore", "--verbose", "-z", "--stdin",
            input="\0".join(paths) + "\0", ok=(0, 1)).split("\0")
    return {f[i + 3]: (f[i], int(f[i + 1]), f[i + 2]) for i in range(0, len(f) - 3, 4)}


# ---------------------------------------------------------------- where a leak lands

def copy_steps(dockerfile):
    """COPY/ADD steps that read the build context. No ARG expansion or heredocs."""
    if not dockerfile.exists():
        return []
    steps, stage, stages, buf, start = [], "", 0, "", 0
    for n, raw in enumerate(dockerfile.read_text(encoding="utf-8").splitlines(), 1):
        s = raw.strip()
        if s.startswith("#") or not (s or buf):
            continue
        start = start if buf else n
        if s.endswith("\\"):
            buf += s[:-1] + " "
            continue
        word, _, rest = (buf + s).partition(" ")
        word, rest, buf = word.upper(), rest.strip(), ""
        if word == "FROM":
            stages += 1
            m = re.search(r"\bAS\s+(\S+)", rest, re.IGNORECASE)
            stage = m.group(1) if m else f"#{stages}"
        elif word in ("COPY", "ADD"):
            flags = re.match(r"(?:--\S+\s+)*", rest).group()
            if "--from=" in flags:
                continue  # reads another stage, not the build context
            body = rest[len(flags):]
            args = json.loads(body) if body.startswith("[") else body.split()
            steps.append((start, stage, stages, args[:-1], f"{word} {rest}"))
    return [Copy(line, st, idx == stages, srcs, text) for line, st, idx, srcs, text in steps]


def copies(step, path):
    for src in step.sources:
        src = (src[2:] if src.startswith("./") else src).rstrip("/")
        if src in ("", "."):
            return True
        if any(ch in src for ch in "*?["):
            parts = path.split("/")
            if any(fnmatch.fnmatchcase("/".join(parts[:k]), src) for k in range(1, len(parts) + 1)):
                return True
        elif path == src or path.startswith(src + "/"):
            return True
    return False


def landing(path, steps):
    """(reaches the final image?, description) for one leaked file."""
    hits = [s for s in steps if copies(s, path)]
    if not hits:
        return False, "sent to Docker, no COPY uses it"
    s = next((s for s in hits if s.final), hits[0])
    where = "final image" if s.final else f"build stage {s.stage}"
    return s.final, f"{where}, Dockerfile:{s.line} {s.text}"


# ---------------------------------------------------------------- --probe

def rules(path):
    """(line, pattern) for each rule in an ignore file. `!` lines un-ignore, so they're skipped."""
    if not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return [(n, s.rstrip()) for n, s in enumerate(lines, 1)
            if s.strip() and not s.startswith(("#", "!"))]


def name_matching(glob):
    """A file name that one glob segment matches, e.g. *.py[cod] -> probe.pyc."""
    out, i = "", 0
    while i < len(glob):
        c = glob[i]
        if c == "*":
            out += "probe"
            while glob[i + 1:i + 2] == "*":
                i += 1
        elif c == "?":
            out += "x"
        elif c == "[" and "]" in glob[i + 2:]:
            end = glob.index("]", i + 2)
            chars = glob[i + 1:end]
            out += next(ch for ch in "xyz_0" if ch not in chars) if chars[0] in "!^" else chars[0]
            i = end
        elif c == "\\" and i + 1 < len(glob):
            i += 1
            out += glob[i]
        else:
            out += c
        i += 1
    return out


def probe_paths(pattern, base, folders):
    """Paths that `pattern`, from the ignore file for folder `base`, should cover."""
    body = pattern.rstrip("/")
    segs = body.split("/")
    inside = pattern.endswith("/") or segs[-1] == "**"  # names a folder: the fake file goes inside
    anywhere = "/" not in body or segs[0] == "**"       # git matches these at any depth below base
    rel = "/".join(name_matching(s) for s in segs if s not in ("", "**"))
    if inside:
        rel = f"{rel}/probe" if rel else "probe"
    if not rel:
        return []
    homes = [f for f in folders if not base or f == base or f.startswith(base + "/")] if anywhere else [base]
    return [f"{home}/{rel}" if home else rel for home in homes]


def build_probe_repo(root, tmp):
    """A throwaway repo with this repo's folders and ignore files, plus a fake file for each rule
    in each folder the rule applies to. Returns {fake file: [(rule file, line, pattern), ...]}."""
    tracked = nul_split(git(root, "ls-files", "-z"))
    folders = {""} | {a for p in tracked for a in ancestors(p)}
    git(tmp, "init", "--quiet")
    for f in folders:
        (tmp / f).mkdir(parents=True, exist_ok=True)
    if (root / ".dockerignore").is_file():
        shutil.copyfile(root / ".dockerignore", tmp / ".dockerignore")

    sources = [(p, root / p, tmp / p, p.rpartition("/")[0]) for p in tracked
               if p.rpartition("/")[2] == ".gitignore"]
    info = Path(git(root, "rev-parse", "--git-path", "info/exclude").strip())
    sources.append((".git/info/exclude", root / info, tmp / ".git/info/exclude", ""))
    configured = git(root, "config", "--path", "core.excludesFile", ok=(0, 1)).strip()
    if configured:
        git(tmp, "config", "core.excludesFile", configured)
    user = Path(configured) if configured else \
        Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "git" / "ignore"
    sources.append((str(user), user, None, ""))  # git reads the user's file in tmp too

    wanted = {}
    for label, src, dest, base in sources:
        if dest and src.is_file():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dest)
        for n, pattern in rules(src):
            for p in probe_paths(pattern, base, folders):
                wanted.setdefault(p, []).append((label, n, pattern))

    parents = {a for p in wanted for a in ancestors(p)}
    tracked = set(tracked)
    probes = {}
    for p, why in wanted.items():
        if p in parents or p in folders:
            p += "/probe"  # something else needs this path to be a folder
        elif p in tracked:
            continue       # git never ignores a tracked file
        probes.setdefault(p, []).extend(why)
    made = {}
    for p, why in probes.items():
        try:
            (tmp / p).parent.mkdir(parents=True, exist_ok=True)
            (tmp / p).touch()
            made[p] = why
        except OSError:
            pass
    return made


# ---------------------------------------------------------------- report

def files(n):
    return f"{n} file" + "s" * (n != 1)


def report(leaks, why, steps, probe):
    """Leaks grouped by the rule git blames: every real path, or one line per rule for fakes."""
    groups = {}
    for p in leaks:
        groups.setdefault(why.get(p, ("?", 0, "?")), []).append(p)
    rows, finals = [], 0
    for (src, line, pattern), paths in sorted(groups.items()):
        where = [landing(p, steps) for p in paths]
        final = [p for p, (f, _) in zip(paths, where) if f]
        finals += len(final)
        rows.append((f"{short(src)}:{line}  {pattern}", paths, where, final))

    if probe:
        width = max(len(r[0]) for r in rows)
        print(f"\n  {'rule':<{width}}  leaks  final image  example")
        for rule, paths, _, final in rows:
            print(f"  {rule:<{width}}  {len(paths):>5}  {len(final):>11}  {(final or paths)[0]}")
    else:
        for rule, paths, where, _ in rows:
            print(f"\n  {rule}")
            for p, (_, text) in list(zip(paths, where))[:SHOW]:
                print(f"      {p:<44}  {text}")
            if len(paths) > SHOW:
                more = sum(f for f, _ in where[SHOW:])
                print(f"      ... and {files(len(paths) - SHOW)} more, {more} into the final image")
    print(f"\n{files(len(leaks))} leaked, {finals} into the final image.")
    print("Cover them in .dockerignore. A bare name there only matches at the root, so write **/name.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--probe", action="store_true", help="test every ignore rule with fake files")
    probe = ap.parse_args().probe

    root = Path(git(Path.cwd(), "rev-parse", "--show-toplevel").strip())
    if shutil.which("docker") is None or subprocess.run(["docker", "info"], capture_output=True).returncode:
        raise CantCheck("Docker isn't running. Start it (`docker desktop start`) and try again.")
    if (root / "Dockerfile.dockerignore").exists():
        raise CantCheck("Dockerfile.dockerignore replaces .dockerignore in real builds, and this check can't see it.")
    steps = copy_steps(root / "Dockerfile")

    if not probe:
        ignored = git_ignores(root)
        leaks = sorted(ignored & docker_gets(root))
        why = blame(root, leaks)
        print(f"git ignores {files(len(ignored))} here. Docker would still get {len(leaks)} of them.")
    else:
        with tempfile.TemporaryDirectory(prefix="probe-context-") as tmp:
            tmp = Path(tmp)
            probes = build_probe_repo(root, tmp)
            ignored = git_ignores(tmp) & set(probes)
            leaks = sorted(ignored & docker_gets(tmp))
            why = blame(tmp, leaks)
        print(f"{files(len(probes))} faked, one per ignore rule per folder it applies to. "
              f"git ignores {len(ignored)}. Docker would still get {len(leaks)} of them.")
    if leaks:
        report(leaks, why, steps, probe)

    if probe:
        tested = {r for p in ignored for r in probes[p]}
        untested = sorted({r for rs in probes.values() for r in rs} - tested)
        if untested:
            print("\nNo fake file for these rules ended up ignored, so they weren't tested:")
            for src, line, pattern in untested:
                print(f"  {short(src)}:{line}  {pattern}")
    return 1 if leaks else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except CantCheck as e:
        print(f"can't check: {e}", file=sys.stderr)
        sys.exit(2)
