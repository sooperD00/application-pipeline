"""
KNOB 1: the data model under test.

This is the thing you're actually trying to falsify. Change it, re-run, look at
the misc pile. When every sample decomposes with an empty misc pile and no
fabricated spans, the model is right and you can go write the SQLModel table.

A note on why every field is required and nothing is Optional
-------------------------------------------------------------
Structured outputs compile your schema into a sampling grammar, and the API caps
you at 24 optional parameters and 16 union-typed parameters across the whole
request. `Optional[str]` is a union (`["string", "null"]`), so a schema built the
natural Python way burns through both budgets fast and 400s with "Schema is too
complex for compilation."

So: everything is required, and absence is the empty string. Ugly in Python,
cheap in grammar. Normalize on the way into Postgres later.
"""

from typing import Literal, List

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# The five shapes, plus the one that matters most.
# ---------------------------------------------------------------------------
# "unclassified" is not a failure state, it is the measurement. If the model is
# forced to pick one of five, it always will, and you will never find out that
# your enum is wrong. Leave the escape hatch open and count how often it's used.

BucketType = Literal[
    "role",           # org + title + dates. job, internship, appointment, fellowship, volunteer post
    "accomplishment",  # one discrete thing you did and what came of it. the only tailorable unit
    "capability",     # a skill noun you claim. not time-bound
    "credential",     # issued by someone else, dated, verifiable, canonical wording
    "narrative",      # prose about you. summary, About, positioning
    "unclassified",   # none of the above — tell me why in `note`
]


class Bucket(BaseModel):
    type: BucketType = Field(
        description="Which of the five shapes this is. Use 'unclassified' freely."
    )
    title: str = Field(
        description="Short human label. For a role, the job title. For an accomplishment, "
        "a 3-8 word handle. For a capability, the skill name itself."
    )
    content: str = Field(
        description="The substance, rewritten as a clean standalone unit that makes sense "
        "with no surrounding document. Do not invent facts not present in the source."
    )
    source_quote: str = Field(
        description="VERBATIM substring copied exactly from the input that this bucket came "
        "from. Must appear character-for-character in the input. This is how coverage is "
        "measured, so do not paraphrase, reflow, or fix typos here."
    )

    # role fields ("" when not a role)
    org: str = Field(description="Organization name, or empty string.")
    start: str = Field(description="Start date as written in the source, or empty string.")
    end: str = Field(description="End date as written, 'present', or empty string.")

    # accomplishment fields ("" when not an accomplishment)
    parent_role_title: str = Field(
        description="If this accomplishment belongs to a role, the EXACT `title` of that "
        "role bucket. Empty string if it stands alone."
    )

    # capability fields ("" when not a capability)
    hedge: str = Field(
        description="Adjacent-experience phrasing for keyword coverage, e.g. 'orchestration "
        "tools like Dagster' when they have Airflow. Empty string if the claim is direct."
    )

    # credential fields ("" when not a credential)
    issuer: str = Field(description="Granting body: university, cert authority, USPTO, journal. Or empty.")
    identifier: str = Field(description="Patent no., DOI, license no., etc. Or empty string.")

    # diagnostics
    section_hint: str = Field(
        description="Where this would RENDER on a document (e.g. 'Experience', 'Publications', "
        "'Skills'). A hint, deliberately not the type — the same credential renders in "
        "different places on a resume vs a CV."
    )
    confidence: float = Field(description="0.0-1.0. How sure you are of the type assignment.")
    note: str = Field(
        description="Required when type is 'unclassified': what this is and why none of the "
        "five fit. Otherwise a short remark or empty string."
    )


class Extraction(BaseModel):
    """One pass over one document."""

    doc_kind: Literal["resume", "cv", "linkedin", "freeform", "other"]
    overall_quality: Literal["low", "medium", "high"] = Field(
        description="Does the content map to a real field, and is it written and structured well?"
    )
    quality_reasoning: str = Field(description="Two sentences maximum.")
    suggested_titles: List[str] = Field(
        description="Up to 5 job titles this person best matches, most likely first."
    )
    buckets: List[Bucket]
    leftover: str = Field(
        description="Anything in the source you could not place in any bucket at all, quoted "
        "verbatim. Empty string if you placed everything. Be honest here — this field is the "
        "point of the exercise."
    )


SCHEMA_VERSION = "v1"  # bump when you change anything above; invalidates the cache
