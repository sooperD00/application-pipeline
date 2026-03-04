"""
tests/test_text_cleaning.py

Pure function tests — no DB, no async, no fixtures.
These should always be green. If they're not, nothing downstream is trustworthy.

Run with: pytest tests/test_text_cleaning.py -v
"""

import pytest
from app.services.text_cleaning import clean_jd_text


# ── Step 1: strip leading/trailing whitespace ─────────────────────────────────

def test_strips_leading_and_trailing_whitespace():
    assert clean_jd_text("  hello  ") == "hello"

def test_strips_leading_newlines():
    assert clean_jd_text("\n\nSenior Engineer\n") == "Senior Engineer"


# ── Step 2: normalize line endings ───────────────────────────────────────────

def test_crlf_becomes_lf():
    assert clean_jd_text("line one\r\nline two") == "line one\nline two"

def test_bare_cr_becomes_lf():
    assert clean_jd_text("line one\rline two") == "line one\nline two"

def test_mixed_line_endings_normalized():
    result = clean_jd_text("a\r\nb\rc\nd")
    assert result == "a\nb\nc\nd"


# ── Step 3: collapse excess newlines ─────────────────────────────────────────

def test_three_newlines_collapse_to_two():
    assert clean_jd_text("a\n\n\nb") == "a\n\nb"

def test_ten_newlines_collapse_to_two():
    assert clean_jd_text("a\n\n\n\n\n\n\n\n\n\nb") == "a\n\nb"

def test_two_newlines_preserved():
    assert clean_jd_text("a\n\nb") == "a\n\nb"

def test_single_newline_preserved():
    assert clean_jd_text("a\nb") == "a\nb"


# ── Step 4: remove non-printable characters ───────────────────────────────────

def test_null_byte_removed():
    assert clean_jd_text("hello\x00world") == "helloworld"

def test_bell_character_removed():
    assert clean_jd_text("hello\x07world") == "helloworld"

def test_tab_preserved():
    # \x09 is tab — explicitly kept
    assert clean_jd_text("col1\tcol2") == "col1\tcol2"

def test_newline_preserved_through_step_4():
    # \x0a is newline — must survive the non-printable strip
    assert "\n" in clean_jd_text("line one\nline two")


# ── Step 5: normalize unicode whitespace ─────────────────────────────────────

def test_non_breaking_space_becomes_regular_space():
    # \xa0 is the #1 LinkedIn/browser paste offender
    result = clean_jd_text("Senior\xa0Engineer")
    assert result == "Senior Engineer"
    assert "\xa0" not in result

def test_em_space_becomes_regular_space():
    result = clean_jd_text("hello\u2003world")
    assert result == "hello world"

def test_en_space_becomes_regular_space():
    result = clean_jd_text("hello\u2002world")
    assert result == "hello world"

def test_em_dash_preserved():
    # em-dash in job titles should survive — it's not whitespace
    result = clean_jd_text("Senior Engineer \u2014 Platform")
    assert "\u2014" in result


# ── Step 6: strip zero-width characters ──────────────────────────────────────

def test_zero_width_space_removed():
    result = clean_jd_text("hello\u200bworld")
    assert result == "helloworld"

def test_bom_removed():
    result = clean_jd_text("\ufeffSenior Engineer")
    assert result == "Senior Engineer"

def test_zero_width_joiner_removed():
    result = clean_jd_text("hello\u200dworld")
    assert result == "helloworld"

def test_soft_hyphen_removed():
    result = clean_jd_text("data\u00adplatform")
    assert result == "dataplatform"


# ── Idempotency ───────────────────────────────────────────────────────────────

def test_idempotent_on_clean_text():
    text = "Senior Data Engineer\n\nWe are looking for someone with 5+ years."
    assert clean_jd_text(clean_jd_text(text)) == clean_jd_text(text)

def test_idempotent_on_messy_text():
    messy = "  hello\xa0world\r\n\n\n\nbye\u200b  "
    assert clean_jd_text(clean_jd_text(messy)) == clean_jd_text(messy)


# ── Edge cases ────────────────────────────────────────────────────────────────

def test_empty_string_returns_empty():
    assert clean_jd_text("") == ""

def test_whitespace_only_returns_empty():
    assert clean_jd_text("   \n\n\t  ") == ""

def test_only_zero_width_chars_returns_empty():
    assert clean_jd_text("\u200b\u200c\ufeff") == ""

def test_realistic_linkedin_paste():
    """
    Approximate what a LinkedIn JD copy-paste looks like in the wild:
    non-breaking spaces, CRLF, excess blank lines.
    """
    raw = (
        "Senior\xa0Data\xa0Engineer\r\n"
        "Acme\xa0Corp\r\n"
        "\r\n"
        "\r\n"
        "\r\n"
        "We\xa0are\xa0hiring!\r\n"
        "\u200b"
    )
    result = clean_jd_text(raw)
    assert "\xa0" not in result
    assert "\r" not in result
    assert "\u200b" not in result
    assert "\n\n\n" not in result
    assert result.startswith("Senior Data Engineer")
