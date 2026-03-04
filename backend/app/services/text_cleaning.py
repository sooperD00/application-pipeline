"""
text_cleaning.py

Six deterministic steps, applied in order on JD ingest.
Raw text is always stored separately (JD.raw_text) for the "view raw" toggle —
this output goes into JD.cleaned_text.

Idempotent: running the pipeline twice returns the same result.
No Claude, no I/O, no state — just string → string.
"""

import re

# ── Compiled once at import time ─────────────────────────────────────────────
# (called up to 25× per session; compiling in a loop is wasteful)

_CRLF = re.compile(r'\r\n|\r')
_EXCESS_NEWLINES = re.compile(r'\n{3,}')
_NON_PRINTABLE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')  # keep \x09=tab \x0a=newline

# Unicode whitespace that isn't a plain ASCII space, tab, or newline.
# These come in from browser pastes — non-breaking spaces (\xa0) are the most
# common offender, but job boards also love em-spaces and line separators.
_UNICODE_WHITESPACE = re.compile(
    r'[\xa0'           # non-breaking space (most common paste artifact)
    r'\u1680'          # ogham space
    r'\u2000-\u200a'   # en space, em space, thin space, and friends
    r'\u2028'          # line separator
    r'\u2029'          # paragraph separator
    r'\u202f'          # narrow no-break space
    r'\u205f'          # medium mathematical space
    r'\u3000]'         # ideographic space (CJK)
)

# Invisible characters — they paste silently and break regex matching downstream.
_ZERO_WIDTH = re.compile(
    r'[\u200b'   # zero-width space
    r'\u200c'    # zero-width non-joiner
    r'\u200d'    # zero-width joiner
    r'\u200e'    # left-to-right mark
    r'\u200f'    # right-to-left mark
    r'\u00ad'    # soft hyphen
    r'\ufeff'    # BOM / zero-width no-break space
    r'\u2060]'   # word joiner
)


# ── Public API ────────────────────────────────────────────────────────────────

def clean_jd_text(raw: str) -> str:
    """
    Apply the six-step pipeline to pasted JD text.

    Steps:
        1. Strip leading/trailing whitespace
        2. Normalize line endings (CRLF and bare CR → LF)
        3. Collapse 3+ consecutive newlines to 2
        4. Remove non-printable ASCII characters (preserve \\t and \\n)
        5. Normalize unicode whitespace to plain ASCII space
        6. Strip zero-width characters
    """
    t = raw
    t = t.strip()                              # 1
    t = _CRLF.sub('\n', t)                     # 2
    t = _EXCESS_NEWLINES.sub('\n\n', t)        # 3
    t = _NON_PRINTABLE.sub('', t)             # 4
    t = _UNICODE_WHITESPACE.sub(' ', t)       # 5
    t = _ZERO_WIDTH.sub('', t)                # 6
    return t
