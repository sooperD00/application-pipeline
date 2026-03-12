/**
 * Tab 1: Scrape & Analyze — /sessions/:id
 *
 * Shows session metadata, JD paste form, and the card grid.
 * Sprint 10 will add the SSE analysis trigger and card animations.
 * For now: paste JDs, see them as gray (pending) cards.
 */
import { useSessionContext } from './SessionLayout'  // so you can reach up to SessionLayout and get contextValue object
import JDPasteForm from '../components/JDPasteForm'
import JDCard from '../components/JDCard'

export default function SessionDetailPage() {
  const { session, jds, refreshSession } = useSessionContext()  // destructure, getting only the 3 values needed here

  return (
    <div>
      
      {/* Session header */}
      {/* - the metadata that defines this search session */}
      <div className="mb-6">
        <h1 className="text-2xl font-semibold mb-1">{session.search_term}</h1>
        <p className="text-pipeline-400 text-sm">
          {session.board} · {session.filters}  {/* e.g. "LinkedIn · remote, last 24 hours"  */}
          <span className="ml-3 text-pipeline-500">
            {session.jd_count} JD{session.jd_count !== 1 ? 's' : ''}  {/* e.g. "3 JDs" or "1 JD" */}
          </span>
        </p>
      </div>

      {/* JD paste form */}
      {/* - add JDs one at a time */}
      <JDPasteForm sessionId={session.id} onAdded={refreshSession} />

      {/* Card grid */}
      {/* one card per JD, sorted by number */}
      {jds.length > 0 && (
        <div className="mt-8">
          <h2 className="text-sm font-medium text-pipeline-400 uppercase tracking-wide mb-3">
            Job Descriptions ({jds.length})  {/* e.g. "Job Descriptions (12)" */}
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {/* "array method chaining" or "array methods" (build in to JS, LINQ equivalent) */}
            {jds
              .slice() // make a shallow copy (don't mutate state directly) (LINQ doesn't mutate the source collection)
              .sort((a, b) => a.number - b.number)  // sort by JD number ascending
              .map((jd) => (  // transform each JD object 
                <JDCard key={jd.id} jd={jd} /> // into rendered card component
              ))}
          </div>
        </div>
      )}

      {/* Stop as soon as you hit a falsy value and render nothing */}
      {/* `&&` for "show/hide" */}
      {/* `condition ? A : B` for "show one or the other" */}
      {jds.length === 0 && ( // JS's short-circuit evaluation
        <p className="mt-8 text-pipeline-500 text-sm">
          No JDs yet. Paste your first job description above.
        </p>
      )}
    </div>
  )
}
