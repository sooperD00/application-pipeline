/**
 * /sessions — Create new sessions (with search metadata) and
 * browse/re-enter existing ones.
 * 
 * A standard index/list page with an inline create form.
 * 
 * Shows all sessions (newest first) with JD count and metadata.
 * Click a row to enter it → navigates to /sessions/:id.
 * Inline "New Session" form at the top.
 */

/* TODO: Sessions go stale as postings expire. Future options:
   - auto-archive after N days
   - manual archive/delete button
   - TTL with a "this session is old, postings may be gone" warning 
*/

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { listSessions } from '../api/client'
import SessionCreateForm from '../components/SessionCreateForm'

export default function SessionsPage() {
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  // cancelled flag pattern = React-specific gotcha
  // like CancellationToken, for when user navigates away fast and component unmounts before the fetch
  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const data = await listSessions()
        if (!cancelled) setSessions(data)
      } catch (err) {
        if (!cancelled) setError(err.detail || err.message)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [])

  function handleCreated(newSession) {
    // Navigate into the new session immediately
    navigate(`/sessions/${newSession.id}`)
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-6">Sessions</h1>

      <SessionCreateForm onCreated={handleCreated} />

      <div className="mt-8">
        {loading && (
          <p className="text-pipeline-400 text-sm">Loading sessions…</p>
        )}

        {error && (
          <p className="text-red-400 text-sm">Error: {error}</p>
        )}

        {!loading && !error && sessions.length === 0 && (
          <p className="text-pipeline-500 text-sm">
            No sessions yet. Create one above to start pasting JDs.
          </p>
        )}

        {sessions.length > 0 && (
          <div className="space-y-2">
            {sessions.map((s) => (
              <button
                key={s.id}
                onClick={() => navigate(`/sessions/${s.id}`)}
                className="w-full text-left px-4 py-3 rounded-lg bg-pipeline-800 hover:bg-pipeline-700 border border-pipeline-700/50 hover:border-pipeline-600 transition-colors group"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-white font-medium group-hover:text-pipeline-100">
                      {s.search_term}
                    </span>
                    <span className="text-pipeline-500 text-sm ml-3">
                      {s.board} · {s.filters}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-pipeline-400">
                    <span>{s.jd_count} JD{s.jd_count !== 1 ? 's' : ''}</span>
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-medium ${
                        s.status === 'complete'
                          ? 'bg-status-apply/20 text-status-apply'
                          : s.status === 'analyzing'
                            ? 'bg-status-maybe/20 text-status-maybe'
                            : 'bg-pipeline-700 text-pipeline-300'
                      }`}
                    >
                      {s.status}
                    </span>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
