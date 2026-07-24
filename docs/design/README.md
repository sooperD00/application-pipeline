# Design Sessions

Feedback lives in `../feedback/` — that's users reporting on a running build.
This folder is different. These are design sessions: two people thinking about
what to build next.

Greg is the PM (Product Manager). Nicole is the sole dev. They are peers. They
keep separate documents in their own language, and confer and give the OK both
ways before anything is integrated into the app.

There is no perfect translation between the two documents. Any translation
instance goes stale the instant it's written, and neither person can hold even
their own objectives and constraints in their head in entirety, let alone each
other's. So neither doc tries to be the merged version. Greg keeps his upstream
in Google Docs; Nicole keeps point-in-time snapshots here alongside her own
notes from the same session.

**These are notes, not a design doc and not requirements. Nothing here is
decided.** The design gets made later, piecemeal — bite only what you can chew
and what you can agree on for the sprint or PR in front of you.

## Conventions

Files are `YYYY-MM-DD-name.md`, one per person per session.

Front matter carries `against:` — the version of the app that existed while the
thinking happened. Note that this means something different here than it does
in `../feedback/`, where it marks what the user was looking at.

Snapshots of an upstream doc carry `snapshot_of:` and `retrieved:`, because the
owner keeps editing it and this copy doesn't follow.

## Comparing the docs

When it's time to check alignment, some version of this:

> Read the files in this folder. Greg is a Product Manager; Nicole is the sole
> dev. They are peers who keep separate documents in their own language, and
> confer and give the OK both ways before code is integrated into the app.
>
> These are notes, not requirements. Nothing in them is decided, and neither
> document is the specification for the other.
>
> Show me where their thinking converges and where it diverges, and on what.
> Vocabulary will differ between the two docs for the same idea — say so when
> you think that's what you're seeing, rather than counting it as a difference.
>
> Divergence is neutral and resolves in either direction: sometimes the roadmap
> moves, sometimes the PM doc gets updated. Don't assume either one is correct.