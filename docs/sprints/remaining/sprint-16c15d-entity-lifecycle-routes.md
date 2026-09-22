# Entity lifecycle and routes

**ID**: `[s-16c15d]`
**Status**: parked
**Phase**: not decided — ADR-016 is titled "(Phase ?)"

JDs graduate from session-scoped to independent entities: `/sessions` stays the funnel,
`/tracking` becomes the index route, and `/pursuits/:jd_id` owns the post-callback workflows.
[ADR-016](../../decisions/adr-016-entity-lifecycle-and-routes.md) is the decision.

A stub on purpose. Nothing gates planning it, so it can be written while other work runs, and
it gives the ideas already aimed this way somewhere to land.

**Watch** ADR-016 is one paragraph: the decision and a sentence of context, with no rationale,
no alternatives, and a title that still asks which phase this is. Planning this sprint is the
moment to append what was missing or to supersede it, while the reasoning is being reconstructed
anyway.

**What points here today**
- [s-77f2e3]'s 404 copy waits for `/tracking` to become the index route, and `NotFoundPage.jsx`
  carries the marker that says so.
- [h-d4b631], the Activities layer, waits for the Full Tracker that `/tracking` would index. It
  stays unassigned until this sprint has a shape that can absorb it.
