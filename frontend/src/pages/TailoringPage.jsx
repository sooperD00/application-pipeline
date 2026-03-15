/**
 * Tab 4: Tailoring — /sessions/:id/tailor
 *
 * Shows all tailoring jobs for the current session, grouped by JD.
 * Primary action: "Batch Tailor All" kicks off tailoring for every
 * apply-status JD that doesn't already have an active job.
 *
 * Per-JD actions: single Tailor button, download docx, download zip package.
 *
 * Polls every 3s while any job is queued or processing. Clears on
 * unmount or when all jobs reach a terminal state (ready/failed/reviewed).
 *
 * Design: vertical list, roomy spacing, download-focused (the real end
 * state is "open in Word," not in-app editing). No in-app preview of
 * resume text — the user downloads and reviews in their own tools.
 * 
 * Lifecycle Management:
 * - useEffect cleanup: return a teardown function → runs on unmount / before re-run
 *   - stopPolling: clearInterval (zombie interval prevention)
 *   - cancelled flag: manual cancellation token (stale setState prevention)
 *   - revokeObjectURL: free browser-allocated memory (GC can't touch it)
 * - useRef (pollRef): mutable box, persists across renders, no re-render on change
 * - useCallback (fetchJobs, handlers): stable function identity for dep arrays
 * - Derived state (applyJds, counts, summaryText): compute during render, not useState
 *
 * Later (Phase N): user has a prompt box next to the zip/docx download links
 * horizontally with that "job" row so they can chat with claude within the
 * context of that specific docx for questions or more substantial revisions
 */
import { useState, useEffect, useCallback, useRef } from 'react'
import { useSessionContext } from './SessionLayout'
import {
  listSessionTailoringJobs,
  batchTailor,
  createTailoringJob,
  downloadTailoringDocx,
  downloadTailoringPackage,
} from '../api/client'

const POLL_INTERVAL_MS = 3000  // 3 seconds

const STATUS_CONFIG = {
  queued:     { label: 'Queued',     color: 'text-pipeline-400', bg: 'bg-pipeline-700',    spin: true },
  processing: { label: 'Processing', color: 'text-yellow-300',   bg: 'bg-yellow-900/30',   spin: true },
  ready:      { label: 'Ready',      color: 'text-green-300',    bg: 'bg-green-900/30',    spin: false },
  reviewed:   { label: 'Reviewed',   color: 'text-blue-300',     bg: 'bg-blue-900/30',     spin: false },
  failed:     { label: 'Failed',     color: 'text-red-300',      bg: 'bg-red-900/30',      spin: false },
}

// ── Helpers ──────────────────────────────────────────────────────────────────

/** Trigger a browser download from a Blob. */
function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)  // browser allocates memory that GC can't touch
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)  // explicitly revoke that memory to prevent memory leak (2GB for 50 resumes in 1 tab = bad)
}

/** True if any job is still in-flight. */
function hasActiveJobs(jobs) {
  return jobs.some(j => j.status === 'queued' || j.status === 'processing')
}

/** Status → display config. */
function statusConfig(status) {
  return STATUS_CONFIG[status] ?? { 
    label: status, color: 'text-pipeline-400', bg: 'bg-pipeline-700', spin: false }
}

// ── Status badge ─────────────────────────────────────────────────────────────

function StatusBadge({ status }) {
  const cfg = statusConfig(status)
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${cfg.bg} ${cfg.color}`}
      data-testid="status-badge"
    >
      {cfg.spin && (
        <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      )}
      {cfg.label}
    </span>
  )
}

// ── Output indicators ────────────────────────────────────────────────────────
// One-liner showing what was generated: "Resume ✓ · Cover letter ✓ · App answers ✓"

function OutputIndicators({ job }) {
  if (job.status !== 'ready' && job.status !== 'reviewed') return null

  const items = []
  if (job.has_docx) items.push('Resume ✓')
  if (job.output_cover_letter) items.push('Cover letter ✓')
  if (job.output_app_answers?.length) items.push('App answers ✓')

  if (items.length === 0) return null

  return (
    <p className="text-xs text-pipeline-400 mt-1" data-testid="output-indicators">
      {items.join(' · ')}
    </p>
  )
}

// ── Job card (one per JD) ────────────────────────────────────────────────────

function TailoringJobCard({ job, onRetry }) {
  const [downloading, setDownloading] = useState(null) // 'docx' | 'package' | null

  const isReady = job.status === 'ready' || job.status === 'reviewed'

  async function handleDownload(type) {
    setDownloading(type)
    try {
      const company = (job.company || 'resume').replace(/\s+/g, '_')
      const role = (job.role || 'tailored').replace(/\s+/g, '_')

      if (type === 'docx') {
        const blob = await downloadTailoringDocx(job.jd_id, job.id)
        downloadBlob(blob, `${company}_${role}.docx`)
      } else {
        const blob = await downloadTailoringPackage(job.jd_id, job.id)
        downloadBlob(blob, `${company}_${role}.zip`)
      }
    } catch (err) {
      console.error(`Download ${type} failed:`, err)
    } finally {
      setDownloading(null)
    }
  }

  return (
    <div
      className="rounded-xl border border-pipeline-700/50 bg-pipeline-800/60 p-5"
      data-testid="tailoring-job-card"
    >
      {/* Header: company/role + status badge */}
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-xs text-pipeline-500 font-mono">#{job.jd_number}</span>
            <h3 className="text-base font-semibold text-pipeline-100 truncate">
              {job.company || 'Unknown Company'}
            </h3>
          </div>
          <p className="text-sm text-pipeline-400 truncate mt-0.5">
            {job.role || 'Unknown Role'}
          </p>
        </div>
        <StatusBadge status={job.status} />
      </div>

      {/* Nullable resume_id notice */}
      {isReady && job.resume_id === null && (
        <p className="text-xs text-yellow-400/70 mt-2">
          Source resume deleted — outputs are still valid.
        </p>
      )}

      {/* Output indicators */}
      <OutputIndicators job={job} />

      {/* Actions row */}
      <div className="flex items-center gap-2 mt-4">
        {/* Download buttons — only when ready */}
        {isReady && (
          <>
            {job.has_docx && (
              <button
                onClick={() => handleDownload('docx')}
                disabled={downloading === 'docx'}
                className="px-3 py-1.5 rounded-lg text-xs font-medium bg-pipeline-700 text-pipeline-200 hover:bg-pipeline-600 transition-colors disabled:opacity-50"
                data-testid="download-docx"
              >
                {downloading === 'docx' ? 'Downloading…' : 'Resume .docx'}
              </button>
            )}
            <button
              onClick={() => handleDownload('package')}
              disabled={downloading === 'package'}
              className="px-3 py-1.5 rounded-lg text-xs font-medium bg-status-apply/20 text-green-300 hover:bg-status-apply/30 transition-colors disabled:opacity-50"
              data-testid="download-package"
            >
              {downloading === 'package' ? 'Downloading…' : 'Download Package (.zip)'}
            </button>
          </>
        )}

        {/* Failed → retry button */}
        {job.status === 'failed' && (
          <button
            onClick={() => onRetry(job.jd_id)}
            className="px-3 py-1.5 rounded-lg text-xs font-medium bg-red-900/40 text-red-300 hover:bg-red-900/60 transition-colors"
            data-testid="retry-button"
          >
            Retry
          </button>
        )}
      </div>
    </div>
  )
}

// ── "Not started" card for apply JDs without a tailoring job ─────────────────

function NotStartedCard({ jd, onTailor, tailoring }) {
  return (
    <div
      className="rounded-xl border border-pipeline-700/30 bg-pipeline-800/30 p-5"
      data-testid="not-started-card"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-xs text-pipeline-500 font-mono">#{jd.number}</span>
            <h3 className="text-base font-semibold text-pipeline-300 truncate">
              {jd.company || 'Unknown Company'}
            </h3>
          </div>
          <p className="text-sm text-pipeline-500 truncate mt-0.5">
            {jd.role || 'Unknown Role'}
          </p>
        </div>
        <span className="text-xs text-pipeline-500 px-2.5 py-1 rounded-full bg-pipeline-800">
          Not started
        </span>
      </div>
      <div className="mt-4">
        <button
          onClick={() => onTailor(jd.id)}
          disabled={tailoring}
          className="px-3 py-1.5 rounded-lg text-xs font-medium bg-status-apply/20 text-green-300 hover:bg-status-apply/30 transition-colors disabled:opacity-50"
          data-testid="tailor-single"
        >
          {tailoring ? 'Starting…' : 'Tailor'}
        </button>
      </div>
    </div>
  )
}

// ── Main page ────────────────────────────────────────────────────────────────

export default function TailoringPage() {
  const { session, jds } = useSessionContext()
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [batchInProgress, setBatchInProgress] = useState(false)
  const [tailoringInFlight, setTailoringInFlight] = useState(new Set())  // useState triggers re-render when updated
  const pollRef = useRef(null) // mutable box that persists across renders without triggering them

  // ── Fetch tailoring jobs ─────────────────────────────────────────────────
  const fetchJobs = useCallback(async () => { // useCallback: stable function reference across renders (needed because it's in useEffect dep arrays)
    try {
      const data = await listSessionTailoringJobs(session.id)
      setJobs(data)
      return data
    } catch (err) {
      setError(err.detail || err.message || 'Failed to load tailoring jobs')
      return []
    }
  }, [session.id])

  // ── Initial load ─────────────────────────────────────────────────────────
  useEffect(() => {
    let cancelled = false // false at the top...
    async function load() {
      setLoading(true)
      await fetchJobs()
      if (!cancelled) setLoading(false)
    }
    load()
    return () => { cancelled = true } // ...true at the bottom = to prevent a race condition if you navigate away
  }, [fetchJobs])

  // ── Polling ──────────────────────────────────────────────────────────────
  // Poll every 3s while any job is queued or processing. Clear when all
  // jobs are terminal or on unmount.
  useEffect(() => {
    function startPolling() {  // the polling effect
      stopPolling()  // clear any existing interval before starting a fresh one (defensive reset)
      pollRef.current = setInterval(async () => {
        const data = await fetchJobs()
        if (!hasActiveJobs(data)) {
          stopPolling()
        }
      }, POLL_INTERVAL_MS)
    }

    function stopPolling() {
      if (pollRef.current) {
        clearInterval(pollRef.current)  // see above: "which calls clearInterval"
        pollRef.current = null
      }
    }

    if (hasActiveJobs(jobs)) {
      startPolling()
    } else {
      stopPolling()
    }

    return stopPolling  // cleanup (so we don't leave a tailoring tab firing fetchJobs() if you navigate away)
  }, [jobs, fetchJobs])

  // ── Batch tailor ─────────────────────────────────────────────────────────
  const handleBatchTailor = useCallback(async () => {
    setError(null)
    setBatchInProgress(true)
    try {
      await batchTailor(session.id)
      // Immediate re-fetch picks up the newly-queued jobs; polling takes over
      await fetchJobs()
    } catch (err) {
      setError(err.detail || err.message || 'Batch tailor failed')
    } finally {
      setBatchInProgress(false)
    }
  }, [session.id, fetchJobs])

  // ── Single JD tailor ─────────────────────────────────────────────────────
  const handleSingleTailor = useCallback(async (jdId) => {
    setError(null)
    setTailoringInFlight(prev => new Set(prev).add(jdId))
    try {
      await createTailoringJob(jdId)
      await fetchJobs()
    } catch (err) {
      setError(err.detail || err.message || 'Tailoring failed')
    } finally {
      setTailoringInFlight(prev => {
        const next = new Set(prev)
        next.delete(jdId)
        return next
      })
    }
  }, [fetchJobs])

  // ── Retry a failed job (creates a new job for the same JD) ───────────────
  const handleRetry = useCallback(async (jdId) => {
    await handleSingleTailor(jdId)
  }, [handleSingleTailor])

  // ── Merge: show job cards for JDs that have jobs, "not started" for the rest
  // Apply-status JDs without a tailoring job get a "not started" card.
// freshness: derive state during render (calculated here, not useState)
  const applyJds = jds.filter(jd => jd.status === 'apply')  // restrict the pool to apply-status only
  const jdIdsWithJobs = new Set(jobs.map(j => j.jd_id))

  // For JDs with jobs, use the latest job (first in array — backend orders by
  // created_at desc within each JD so "first encountered" = newest).
  const latestJobByJd = new Map()
  for (const job of jobs) {
    // First seen = newest (backend orders created_at desc) — skip older jobs for same JD
    if (!latestJobByJd.has(job.jd_id)) { // latestJobByJd map deduplicates by JD (first = newest, backend orders desc)
      latestJobByJd.set(job.jd_id, job)
    }
  }

  // Summary counts
  const counts = { queued: 0, processing: 0, ready: 0, failed: 0 }
  for (const job of latestJobByJd.values()) {
    if (counts[job.status] !== undefined) counts[job.status]++
  }

  const summaryText = [
    counts.ready      && `${counts.ready} ready`,
    counts.processing && `${counts.processing} processing`,
    counts.queued     && `${counts.queued} queued`,
    counts.failed     && `${counts.failed} failed`,
  ].filter(Boolean).join(' · ')

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-pipeline-400 text-sm">Loading tailoring jobs…</div>
      </div>
    )
  }

  return (
    <div>
      {/* Page header */}
      <div className="mb-6">
        <h1 className="text-2xl font-semibold mb-1">Tailoring</h1>
        <p className="text-pipeline-400 text-sm">
          Tailored resumes, cover letters, and application answers.
          Download the package and open in Word.
        </p>
      </div>

      {/* Error banner */}
      {error && (
        <div
          className="mb-4 px-4 py-3 rounded-lg bg-red-900/30 border border-red-700/50"
          data-testid="error-banner"
        >
          <p className="text-sm text-red-300">{error}</p>
        </div>
      )}

      {/* Batch Tailor All + summary */}
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={handleBatchTailor}
          disabled={batchInProgress || applyJds.length === 0}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            batchInProgress || applyJds.length === 0
              ? 'bg-pipeline-700 text-pipeline-500 cursor-not-allowed'
              : 'bg-status-apply text-white hover:bg-status-apply/80'
          }`}
          data-testid="batch-tailor-button"
        >
          {batchInProgress ? 'Starting…' : 'Batch Tailor All'}
        </button>

        {/* Summary chips */}
        {summaryText && (
          <span className="text-xs text-pipeline-400" data-testid="tailoring-summary">
            {summaryText}
          </span>
        )}
      </div>

      {/* Job list — vertical, roomy */}
      <div className="space-y-4">
        {/* JDs with tailoring jobs (sorted by jd_number) */}
        {Array.from(latestJobByJd.values())
          .sort((a, b) => a.jd_number - b.jd_number)
          .map(job => (
            <TailoringJobCard
              key={job.id}
              job={job}
              onRetry={handleRetry}
            />
          ))
        }

        {/* Apply JDs without jobs — "not started" cards */}
        {applyJds
          .filter(jd => !jdIdsWithJobs.has(jd.id)) // apply JDs that don't already have a tailoring job
          .sort((a, b) => a.number - b.number)
          .map(jd => (
            <NotStartedCard
              key={jd.id}
              jd={jd}
              onTailor={handleSingleTailor}
              tailoring={tailoringInFlight.has(jd.id)}
            />
          ))
        }
      </div>

      {/* Empty state */}
      {applyJds.length === 0 && jobs.length === 0 && (
        <p className="mt-8 text-pipeline-500 text-sm">
          No apply-status JDs in this session. Run analysis first, then come back here.
        </p>
      )}
    </div>
  )
}
