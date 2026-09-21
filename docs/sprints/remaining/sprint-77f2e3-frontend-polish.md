# Frontend polish

**ID**: `[s-77f2e3]`
**Status**: parked
**Phase**: 1

**Kind:** decide when it gets planned. A grab-bag has no single ordering heuristic, and choosing
one now would be pretending.

Quarantined UI and product judgment: ideas I am not ready to finalize, kept here so they are not
lost and do not leak into sprints that have real functionality and quality work to do. Nothing
in this list blocks anything.

**Scope**
- [ ] Make the JD cards an actual playing-card aspect ratio — they are longer horizontally
      today — then spread them like a ribbon instead of not overlapping at all. Generous, equal
      spacing before analysis, so the start of each title and subtitle is readable. After
      analysis: Apply cards trickled to the left with no overlap, Maybe ribbon-spread in the
      middle at medium overlap, No spread tight on the right at high overlap
- [ ] Card grid sort: once analysis starts, sort by [status_priority, number] instead of number
      alone, so Apply cards float to the top after each `batch_complete` and the user sees which
      JDs survived in real time. Toggle on session status — by number while active, since paste
      order matters during data entry, by status while analyzing or complete. Small change to
      SessionDetailPage's `mergedJds` sort comparator
- [ ] Edit and delete JD cards in `sessions/:id`, reusing the resume card implementation
- [ ] Show the Claude analysis per JD somewhere. There is no place to read it today, and it is
      usually a good chart of skill matches plus a summary
- [ ] "Download all" button — a zip laid out as
      `session_title_timestamp/[company_role_timestamp]/[files]`, so a user who trusts the
      output can take everything at once, open it, check it themselves and apply
- [ ] Add a meta analysis over the tailored resumes — all of them, or at least within one
      session — answering whether tailoring was worth it. Tells me as the dev how worthwhile
      this part of the tool is, and tells the user their money did something beyond what the
      analyze phase already said. Could be as simple as sending the finished resumes and JDs
      through a fresh Claude call and displaying the result in a box
- [ ] Move or duplicate Tab 4's "Batch Tailor All" onto Tab 1 next to Analyze — placement
      decision, not a feature
- [ ] Flag jobs whose JD status changed after tailoring (apply → maybe). They still show on
      Tab 4, which is intentional since the output exists, but a "JD status changed to maybe"
      indicator would explain why it is there
- [ ] Say "Re-analyze" instead of "Analyze" when `session.status === 'complete'`
- [ ] Render MetaAnalysis as markdown. It is whitespace-pre-wrap plain text today, so bold and
      lists would not render — fine while the analysis prompt doesn't ask for markdown, and a
      lightweight renderer is the fix when it does
- [ ] JDPasteForm: auto-populate company and role from the first lines of the pasted text, while
      nothing on the Claude side extracts them (marked in source)
- [ ] JDPasteForm: make the submit shortcut a user preference — Enter today, Cmd/Ctrl+Enter the
      alternative. Both implementations are in the file, one commented out, with the case for
      each (marked in source)
- [ ] JDPasteForm: once Claude analysis extracts company and role from `raw_text`, show them
      pre-populated and editable rather than as manual entry, and decide whether to
      de-emphasize the fields (marked in source)
- [ ] NotFoundPage: update the 404 copy once `/tracking` becomes the index route (ADR-016
      scope) (marked in source)
- [ ] Replace the browser-native `title` tooltip on locked tabs — "Select or create a session to
      unlock this step" — with a custom component. The 1s delay is hardcoded in the browser, not
      in the app, so a component is the only way to make it feel instant
- [ ] Load Inter and JetBrains Mono, or stop naming them. Tailwind's `@theme` references both
      and nothing fetches them, so the app renders in system fonts. Add a `<link>` to index.html
      when typography starts to matter — or never, if system fonts are fine
- [ ] Give the app its own favicon. `index.html` still links Vite's logo (`public/vite.svg`), and
      a tab kept open through a whole session should be findable at a glance. Replace the file
      and the link together
- [ ] Retry UX on the SessionLayout fetch. A transient error currently means navigating away and
      back; a retry button is the whole fix
- [ ] Loading skeleton or optimistic insert on addJD. The card grid waits for `refreshSession()`
      to resolve, which is fine locally and may not be in production
- [ ] Guard unsaved changes on the resume form. Clicking Edit mid-create silently overwrites
      what was typed
- [ ] Session picker: the /sessions list page is the picker today, and it is simpler and
      sufficient. A nav dropdown was in an old sprint spec and is deferred, not dropped — if it
      comes back it reads from the same `listSessions()` endpoint
