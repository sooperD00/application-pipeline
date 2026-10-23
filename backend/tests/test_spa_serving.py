"""
tests/test_spa_serving.py

The SPA catch-all in main.py maps any unmatched path to a file in static/. These tests pin
the one rule that matters: it never maps a path to a file outside static/. No database, no
app routes -- just _spa_file against a throwaway directory.

Run:
    pytest tests/test_spa_serving.py -v
"""

import pytest

from app.main import _spa_file


@pytest.fixture
def static_dir(tmp_path):
    """static/ with an index, a root-level file, and a secret one level above it."""
    static = tmp_path / "static"
    (static / "assets").mkdir(parents=True)
    (static / "index.html").write_text("<html>spa</html>")
    (static / "vite.svg").write_text("<svg/>")
    (static / "assets" / "app.js").write_text("x")
    (tmp_path / "secret.txt").write_text("outside static")
    return static


# ── Paths the app is supposed to serve ───────────────────────────────────────


def test_root_level_file_is_served(static_dir):
    assert _spa_file(static_dir, "vite.svg") == (static_dir / "vite.svg").resolve()


def test_nested_file_is_served(static_dir):
    assert _spa_file(static_dir, "assets/app.js") == (static_dir / "assets" / "app.js").resolve()


@pytest.mark.parametrize("path", ["", "sessions", "sessions/123", "sessions/123/tailoring"])
def test_client_routes_get_index(static_dir, path):
    """React Router owns these; the server just hands back the app shell."""
    assert _spa_file(static_dir, path) == (static_dir / "index.html").resolve()


# ── Paths that must never leave static/ ──────────────────────────────────────


@pytest.mark.parametrize(
    "path",
    [
        "../secret.txt",           # GET /../secret.txt sent with --path-as-is
        "assets/../../secret.txt", # climbs out from inside a subfolder
        "/etc/passwd",             # GET //etc/passwd: absolute path replaces static_dir
        "/proc/self/environ",      # same shape, aimed at the process environment
    ],
)
def test_escaping_paths_get_index(static_dir, path):
    assert _spa_file(static_dir, path) == (static_dir / "index.html").resolve()


def test_symlink_out_of_static_gets_index(static_dir, tmp_path):
    link = static_dir / "link.txt"
    try:
        link.symlink_to(tmp_path / "secret.txt")
    except OSError:
        pytest.skip("this machine can't create symlinks (Windows without Developer Mode)")
    assert _spa_file(static_dir, "link.txt") == (static_dir / "index.html").resolve()


def test_nul_byte_gets_index_not_an_error(static_dir):
    """%00 in a URL decodes to a NUL, which pathlib refuses with ValueError."""
    assert _spa_file(static_dir, "index.html\x00.png") == (static_dir / "index.html").resolve()
