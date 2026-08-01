"""Loads and validates config.toml.

No values live here — they live in the TOML. This file validates e.g.
"2.6" on import and flags error naming the field.

Names are exported flat and uppercase so call sites read the way they did when
these were module constants: `from config import CHARS_PER_TOKEN`.
"""

from __future__ import annotations

import tomllib
from datetime import date
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

_PATH = Path(__file__).parent / "config.toml"


class Strict(BaseModel):
    """Lax pydantic silently coerces the string "2.6" into a 2.6 typo (e.g.
    from a hand-edited TOML). Strict rejects it. int-for-float still passes,
    so `coverage_floor = 85` needs no decimal point."""
    model_config = ConfigDict(strict=True)


# ---------------------------------------------------------------------------
# shape
# ---------------------------------------------------------------------------

class Tier(Strict):
    """One pricing period. USD per million tokens."""
    input: float = Field(gt=0)
    output: float = Field(gt=0)
    until: date | None = None   # last day this tier applies; None = open-ended


class Price(Strict):
    tiers: list[Tier] = Field(min_length=1)

    def on(self, when: date) -> Tier:
        for t in self.tiers:
            if t.until is None or when <= t.until:
                return t
        return self.tiers[-1]   # every tier expired; the last one is the fallback


class OutRate(Strict):
    """Output tokens per document character. Ordered lo <= mid <= hi."""
    lo: float = Field(gt=0)
    mid: float = Field(gt=0)
    hi: float = Field(gt=0)

    @model_validator(mode="after")
    def _ordered(self):
        if not self.lo <= self.mid <= self.hi:
            raise ValueError(f"must be lo <= mid <= hi, got {self.lo}/{self.mid}/{self.hi}")
        return self


class Estimate(Strict):
    chars_per_token: float = Field(gt=0)
    out_per_doc_char: dict[str, OutRate]

    def out_rate(self, model: str) -> OutRate:
        return self.out_per_doc_char.get(model, self.out_per_doc_char["default"])

    def measured(self, model: str) -> bool:
        return model in self.out_per_doc_char


class Run(Strict):
    default_model: str
    max_tokens: int = Field(gt=0)


class Thresholds(Strict):
    truncate_at: float = Field(gt=0, le=1)
    big_file_bytes: int = Field(gt=0)
    coverage_floor: float = Field(ge=0, le=100)


class Intake(Strict):
    allowed_file_types: list[str]


class Config(Strict):
    estimate: Estimate
    prices: dict[str, Price]
    run: Run
    thresholds: Thresholds
    intake: Intake


# ---------------------------------------------------------------------------
# load
# ---------------------------------------------------------------------------

with open(_PATH, "rb") as fh:
    CONFIG = Config.model_validate(tomllib.load(fh))

ESTIMATE = CONFIG.estimate
PRICES = CONFIG.prices

CHARS_PER_TOKEN = ESTIMATE.chars_per_token
DEFAULT_MODEL = CONFIG.run.default_model
MAX_TOKENS = CONFIG.run.max_tokens
TRUNCATE_AT = CONFIG.thresholds.truncate_at
BIG_FILE_BYTES = CONFIG.thresholds.big_file_bytes
COVERAGE_FLOOR = CONFIG.thresholds.coverage_floor
ALLOWED_FILE_TYPES = set(CONFIG.intake.allowed_file_types)   # TOML has no sets


def dollars(model: str, tok_in: int, tok_out: int, when: date | None = None):
    """(cost, tier) for a call, or (None, None) if the model isn't priced.

    Returns None rather than raising: an unpriced model should cost you the
    dollar estimate, not the run.
    """
    price = PRICES.get(model)
    if price is None:
        return None, None
    t = price.on(when or date.today())
    return (tok_in * t.input + tok_out * t.output) / 1_000_000, t