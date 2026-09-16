"""[SPRINT-13-CLEANUP] Tests for scripts/dep_freeze.py, which is Sprint 13 scaffolding.

Delete alongside the module at 13c close -- see remaining-sprints.md, Sprint 13c.
"""

import pytest

from scripts.dep_freeze import (
    BEGIN,
    END,
    diff_pins,
    normalize_name,
    parse_freeze,
    render_constraints,
    replace_block,
    unparsed_lines,
)


class TestNormalizeName:
    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("Jinja2", "jinja2"),
            ("SQLAlchemy", "sqlalchemy"),
            ("typing_extensions", "typing-extensions"),
            ("docstring_parser", "docstring-parser"),
            ("pydantic_core", "pydantic-core"),
            ("zope.interface", "zope-interface"),
            ("ruamel.yaml.clib", "ruamel-yaml-clib"),
            ("  spaced  ", "spaced"),
        ],
    )
    def test_pep503(self, raw, expected):
        assert normalize_name(raw) == expected

    def test_separator_runs_collapse(self):
        assert normalize_name("weird__name..here") == "weird-name-here"


class TestParseFreeze:
    def test_crlf_and_mixed_case(self):
        text = "SQLAlchemy==2.0.47\r\nsqlmodel==0.0.37\r\n"
        assert parse_freeze(text) == {"sqlalchemy": "2.0.47", "sqlmodel": "0.0.37"}

    def test_skips_comments_blanks_and_flags(self):
        text = "\n".join(
            [
                "# a comment",
                "",
                "   ",
                "-e git+https://example.com/pkg#egg=pkg",
                "--index-url https://example.com/simple",
                "fastapi==0.134.0",
            ]
        )
        assert parse_freeze(text) == {"fastapi": "0.134.0"}

    def test_skips_direct_reference(self):
        text = "local-thing @ file:///c:/tmp/local-thing\nalembic==1.18.4\n"
        assert parse_freeze(text) == {"alembic": "1.18.4"}

    def test_strips_environment_marker(self):
        text = 'colorama==0.4.6 ; sys_platform == "win32"\n'
        assert parse_freeze(text) == {"colorama": "0.4.6"}

    def test_trailing_line_without_newline(self):
        assert parse_freeze("python-docx==1.2.0") == {"python-docx": "1.2.0"}

    def test_last_wins_on_duplicate(self):
        assert parse_freeze("pytest==8.0.0\npytest==9.0.2\n") == {"pytest": "9.0.2"}


class TestUnparsedLines:
    def test_surfaces_only_the_silently_dropped(self):
        text = "\n".join(
            [
                "# comment",
                "",
                "fastapi==0.134.0",
                "local-thing @ file:///c:/tmp/local-thing",
                "-e .",
            ]
        )
        assert unparsed_lines(text) == [
            "local-thing @ file:///c:/tmp/local-thing",
            "-e .",
        ]

    def test_clean_freeze_has_none(self):
        assert unparsed_lines("fastapi==0.134.0\nuvicorn==0.41.0\n") == []


class TestRenderConstraints:
    def test_sorted_and_quoted(self):
        block = render_constraints({"uvicorn": "0.41.0", "alembic": "1.18.4"})
        assert block == "\n".join(
            [
                "constraint-dependencies = [",
                '    "alembic==1.18.4",',
                '    "uvicorn==0.41.0",',
                "]",
            ]
        )

    def test_empty_pins_still_valid_toml_shape(self):
        assert render_constraints({}) == "constraint-dependencies = [\n]"


class TestReplaceBlock:
    TEMPLATE = "\n".join(
        [
            "[tool.uv]",
            "package = false",
            BEGIN,
            "constraint-dependencies = [",
            "]",
            END,
            "",
            "[tool.pytest.ini_options]",
        ]
    )

    def test_inserts_between_sentinels(self):
        block = render_constraints({"alembic": "1.18.4"})
        result = replace_block(self.TEMPLATE, block)
        assert '    "alembic==1.18.4",' in result
        assert result.count(BEGIN) == 1
        assert result.count(END) == 1
        assert result.endswith("[tool.pytest.ini_options]")

    def test_is_idempotent(self):
        block = render_constraints({"alembic": "1.18.4"})
        once = replace_block(self.TEMPLATE, block)
        assert replace_block(once, block) == once

    def test_leaves_surrounding_content_alone(self):
        result = replace_block(self.TEMPLATE, render_constraints({"x": "1"}))
        assert result.startswith("[tool.uv]\npackage = false\n")

    def test_missing_sentinels_raises(self):
        with pytest.raises(ValueError, match="sentinels not found"):
            replace_block("[tool.uv]\npackage = false\n", "constraint-dependencies = [\n]")

    def test_reversed_sentinels_raises(self):
        reversed_text = "\n".join([END, "constraint-dependencies = [", "]", BEGIN])
        with pytest.raises(ValueError, match="before BEGIN"):
            replace_block(reversed_text, "constraint-dependencies = [\n]")


class TestDiffPins:
    def test_identical_is_empty(self):
        pins = {"fastapi": "0.134.0", "alembic": "1.18.4"}
        assert diff_pins(pins, dict(pins)) == ([], [], [])

    def test_case_difference_is_not_a_change(self):
        """The whole reason this module exists instead of `diff`."""
        baseline = parse_freeze("SQLAlchemy==2.0.47\nMako==1.3.10\n")
        candidate = parse_freeze("sqlalchemy==2.0.47\nmako==1.3.10\n")
        assert diff_pins(baseline, candidate) == ([], [], [])

    def test_underscore_difference_is_not_a_change(self):
        baseline = parse_freeze("typing_extensions==4.15.0\n")
        candidate = parse_freeze("typing-extensions==4.15.0\n")
        assert diff_pins(baseline, candidate) == ([], [], [])

    def test_added_removed_changed(self):
        baseline = {"a": "1.0", "b": "2.0", "c": "3.0"}
        candidate = {"a": "1.0", "b": "2.1", "d": "4.0"}
        assert diff_pins(baseline, candidate) == (["d"], ["c"], ["b"])

    def test_lxml_appearing_reads_as_added(self):
        """The expected 13a diff: uv export declares what pip pulled in transitively."""
        baseline = parse_freeze("python-docx==1.2.0\n")
        candidate = parse_freeze("python-docx==1.2.0\nlxml==6.0.2\n")
        added, removed, changed = diff_pins(baseline, candidate)
        assert added == ["lxml"]
        assert (removed, changed) == ([], [])
