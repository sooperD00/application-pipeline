/**
 * SessionLayout — the shell for all /sessions/:id/* routes.
 *
 * "Fetch once at the layout level, share the result with all child routes, 
 * and give them a way to trigger a refresh."
 * 
 * Reads the session ID from the URL (useParams), fetches the full session
 * with JDs, and passes it to child routes via Outlet context. Child pages
 * call useSessionContext() instead of fetching independently.
 * 
 * The URL is untrusted input, but that's fine because the backend is the actual gatekeeper
 *
 * This is NOT a global context provider — it's scoped to the layout and
 * lives below the URL params, which remain the source of truth. See the
 * Sprint 8 rationale in remaining-sprints.md for why URL > context.
 */
import { useState, useEffect, useCallback, createContext, useContext } from 'react'
import { useParams, Outlet } from 'react-router-dom'
import { getSession } from '../api/client'

const SessionContext = createContext(null)

/**
 * Hook for child routes to access session data + refresh callback.
 *
 * Returns { session, jds, loading, error, refreshSession }
 * where `session` is the SessionWithJDs response and `jds` is
 * a convenience alias for session.jds.
 */
export function useSessionContext() {
  const ctx = useContext(SessionContext)
  if (!ctx) {
    throw new Error('useSessionContext must be used inside <SessionLayout>')
  }
  return ctx
}

export default function SessionLayout() {
  const { id } = useParams()
  const [session, setSession] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchSession = useCallback(async () => {
    try {
      setError(null)
      const data = await getSession(id)
      setSession(data)
    } catch (err) {
      setError(err.detail || err.message || 'Failed to load session')
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    setLoading(true)
    fetchSession()
  }, [fetchSession])

  // refreshSession: child pages call this after mutations (e.g. addJD)
  // so the card grid updates without a full page reload.
  // useCallback = "only recreate this function when id changes" (cache key)
  const refreshSession = useCallback(() => { 
    return fetchSession()
  }, [fetchSession])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-pipeline-400 text-sm">Loading session…</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-red-400 text-sm">
          {error === 'Session not found'
            ? 'Session not found. It may have been deleted.'
            : `Error: ${error}`}
        </div>
      </div>
    )
  }

  const contextValue = {
    session,
    jds: session?.jds ?? [],
    loading,
    error,
    refreshSession,
  }

  return (
    <SessionContext.Provider value={contextValue}>
      <Outlet />
    </SessionContext.Provider>
  )
}
