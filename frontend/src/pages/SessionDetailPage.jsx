/**
 * Tab 1: Scrape & Analyze — /sessions/:id
 *
 * Shows session metadata, JD paste form, card grid, and (Sprint 10)
 * the Analyze button that kicks off batch analysis via SSE.
 *
 * SSE flow: click Analyze → analyzeSession() returns a raw Response →
 * useSSE.consume() parses the stream → callbacks patch local state →
 * cards animate from gray to green/yellow/red in real time →
 * analysis_complete fires → refreshSession() syncs canonical state.
 *
 * State layering: during streaming, jdOverrides holds partial updates
 * from jd_result events. These merge on top of the context jds for
 * rendering. Once analysis_complete fires, refreshSession() pulls
 * the full state from the backend and the overrides become redundant.
 */
import { useState, useCallback, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useSessionContext } from './SessionLayout'
import { analyzeSession } from '../api/client'
import useSSE from '../hooks/useSSE'
import JDPasteForm from '../components/JDPasteForm'
import JDCard from '../components/JDCard'
import MetaAnalysis from '../components/MetaAnalysis'

export default function SessionDetailPage() {
  const { session, jds, refreshSession } = useSessionContext()

  // ── SSE streaming state ──────────────────────────────────────────────────
  // These overlay on top of context jds during analysis. Once the stream
  // finishes and refreshSession() runs, the context catches up and the
  // overrides become stale (harmless — same data).
  const [jdOverrides, setJdOverrides] = useState({})     // { [jd_id]: { status, analysis_text } }
  const [metaAnalysis, setMetaAnalysis] = useState(session.meta_analysis || null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisSummary, setAnalysisSummary] = useState(null)  // { apply, maybe, no }
  const [error, setError] = useState(null)               // string — red banner with retry
  const [banner, setBanner] = useState(null)              // { type, message, link?, linkText? } — amber banner

  const { consume, abort } = useSSE()

  // Clean up stream if user navigates away mid-analysis
  useEffect(() => {
    return () => abort()
  }, [abort])

  // Sync meta_analysis from context when session refreshes
  // (e.g., returning to a completed session)
  useEffect(() => {
    if (session.meta_analysis && !isAnalyzing) {
      setMetaAnalysis(session.meta_analysis)
    }
  }, [session.meta_analysis, isAnalyzing])

  const handleAnalyze = useCallback(async () => {
    // Reset for a fresh run
    setError(null)
    setBanner(null)
    setJdOverrides({})
    setAnalysisSummary(null)
    setIsAnalyzing(true)

    try {
      const response = await analyzeSession(session.id)

      await consume(response, {
        // Callback keys match backend event names directly —
        // useSSE dispatches via callbacks[event]?.(data), zero mapping needed.

        batch_start: () => {
          // Could show "Analyzing batch N..." — not needed for MVP.
          // The card animations tell the story.
        },

        jd_result: (data) => {
          setJdOverrides(prev => ({
            ...prev,
            [data.jd_id]: {
              status: data.status,
              analysis_text: data.analysis,
            },
          }))
        },

        batch_complete: (data) => {
          setMetaAnalysis(data.meta_analysis)
        },

        analysis_complete: (data) => {
          setAnalysisSummary(data.summary)
          refreshSession()  // sync canonical state from backend
        },

        error: (data) => {
          // "No resume found" → amber banner with link to /resumes
          // Everything else → red error banner with retry
          if (data.message?.toLowerCase().includes('resume')) {
            setBanner({
              type: 'warning',
              message: data.message,
              link: '/resumes',
              linkText: 'Go to Resumes →',
            })
          } else {
            setError(data.message || 'Analysis failed. Click Analyze to retry.')
          }
        },
      })
    } catch (err) {
      // HTTP-level errors (thrown before streaming starts)
      if (err.status === 422 && err.detail?.toLowerCase().includes('resume')) {
        // Defensive: in case a future backend change moves the resume check
        // to an HTTP error instead of an SSE error
        setBanner({
          type: 'warning',
          message: err.detail,
          link: '/resumes',
          linkText: 'Go to Resumes →',
        })
      } else if (err.status === 422 || err.status === 409) {
        setBanner({
          type: 'warning',
          message: err.detail || 'Cannot analyze right now.',
        })
      } else {
        setError(err.detail || err.message || 'Failed to start analysis.')
      }
    } finally {
      setIsAnalyzing(false)
    }
  }, [session.id, consume, refreshSession])

  // ── Merge SSE overrides onto context jds ─────────────────────────────────
  // During streaming: context jds have status=pending, overrides have the
  // real status from Claude. After refreshSession: context catches up and
  // overrides are the same data. Spread order: context first, override wins.
  const mergedJds = jds.map(jd => {
    const override = jdOverrides[jd.id]
    return override ? { ...jd, ...override } : jd
  })

  const analyzeDisabled = isAnalyzing || session.status === 'analyzing'

  return (
    <div>

      {/* Session header */}
      <div className="mb-6">
        <h1 className="text-2xl font-semibold mb-1">{session.search_term}</h1>
        <p className="text-pipeline-400 text-sm">
          {session.board} · {session.filters}
          <span className="ml-3 text-pipeline-500">
            {session.jd_count} JD{session.jd_count !== 1 ? 's' : ''}
          </span>
        </p>
      </div>

      {/* Error banner — red, with retry button (API/SSE failures) */}
      {error && (
        <div
          className="mb-4 px-4 py-3 rounded-lg bg-red-900/30 border border-red-700/50 flex items-center justify-between"
          data-testid="error-banner"
        >
          <p className="text-sm text-red-300">{error}</p>
          <button
            onClick={handleAnalyze}
            className="ml-4 shrink-0 text-sm font-medium text-red-200 hover:text-white underline"
          >
            Retry
          </button>
        </div>
      )}

      {/* Warning banner — amber, with optional link (422 no resumes, 409 conflict) */}
      {banner && (
        <div
          className="mb-4 px-4 py-3 rounded-lg bg-yellow-900/30 border border-yellow-700/50"
          data-testid="warning-banner"
        >
          <p className="text-sm text-yellow-300">
            {banner.message}
            {banner.link && (
              <Link
                to={banner.link}
                className="ml-2 font-medium text-yellow-200 hover:text-white underline"
              >
                {banner.linkText}
              </Link>
            )}
          </p>
        </div>
      )}

      {/* JD paste form */}
      <JDPasteForm sessionId={session.id} onAdded={refreshSession} />

      {/* Analyze button + summary chips */}
      {jds.length > 0 && (
        <div className="mt-4 flex items-center gap-3">
          <button
            onClick={handleAnalyze}
            disabled={analyzeDisabled}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              analyzeDisabled
                ? 'bg-pipeline-700 text-pipeline-500 cursor-not-allowed'
                : 'bg-status-apply text-white hover:bg-status-apply/80'
            }`}
            data-testid="analyze-button"
          >
            {isAnalyzing ? 'Analyzing…' : 'Analyze'}
          </button>

          {/* Summary chips — appear after analysis_complete */}
          {analysisSummary && (
            <span className="text-xs text-pipeline-400" data-testid="analysis-summary">
              {analysisSummary.apply} apply · {analysisSummary.maybe} maybe · {analysisSummary.no} no
            </span>
          )}
        </div>
      )}

      {/* Card grid — mergedJds so cards animate during streaming */}
      {mergedJds.length > 0 && (
        <div className="mt-8">
          <h2 className="text-sm font-medium text-pipeline-400 uppercase tracking-wide mb-3">
            Job Descriptions ({mergedJds.length})
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {mergedJds
              .slice()
              .sort((a, b) => a.number - b.number)
              .map((jd) => (
                <JDCard key={jd.id} jd={jd} />
              ))}
          </div>
        </div>
      )}

      {/* Meta analysis panel — updates after each batch_complete */}
      <MetaAnalysis text={metaAnalysis} />

      {jds.length === 0 && (
        <p className="mt-8 text-pipeline-500 text-sm">
          No JDs yet. Paste your first job description above.
        </p>
      )}
    </div>
  )
}
