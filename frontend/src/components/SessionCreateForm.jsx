/**
 * SessionCreateForm — inline form on the Sessions list page.
 *
 * Three fields matching the Session model: board, filters, search_term.
 * On submit, calls createSession() and passes the new session to onCreated.
 * The parent (SessionsPage) handles navigation.
 */
import { useState } from 'react'
import { createSession } from '../api/client'

export default function SessionCreateForm({ onCreated }) {
  // const [value, setter] = default value
  const [open, setOpen] = useState(false)  // boolean to control whether the form is visible. start with button, then show form.
  const [board, setBoard] = useState('LinkedIn')
  const [filters, setFilters] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!searchTerm.trim()) return

    setSubmitting(true)
    setError(null)
    try {
      const session = await createSession({
        board: board.trim(),
        filters: filters.trim(),
        search_term: searchTerm.trim(),
      })
      // Reset form
      setBoard('LinkedIn')
      setFilters('')
      setSearchTerm('')
      setOpen(false)
      onCreated(session)
    } catch (err) {
      setError(err.detail || err.message || 'Failed to create session')
    } finally {
      setSubmitting(false)
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="px-4 py-2 rounded-lg bg-pipeline-700 text-white text-sm font-medium hover:bg-pipeline-600 transition-colors"
      >
        + New Session
      </button>
    )
  }

  return (
    <div className="p-4 rounded-lg bg-pipeline-800 border border-pipeline-700/50">

      {/* Form Title */}
      <h2 className="text-sm font-medium text-pipeline-300 mb-3">New Search Session</h2>
      {/* no <form> tag — React event handlers only (artifact constraint) */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">

        {/* Job Board */}
        <div>
          <label htmlFor="session-board" className="block text-xs text-pipeline-400 mb-1">
            Board
          </label>
          <select
            id="session-board"
            value={board}
            onChange={(e) => setBoard(e.target.value)}
            className="w-full px-3 py-2 rounded bg-pipeline-900 border border-pipeline-600 text-pipeline-100 text-sm focus:outline-none focus:border-pipeline-400"
          >
            <option>LinkedIn</option>
            <option>Indeed</option>
            <option>Welcome to the Jungle</option>
            <option>Otta</option>
            <option>Other</option>
          </select>
        </div>

        {/* Job Board Filter Description */}
        <div>
          <label htmlFor="session-filters" className="block text-xs text-pipeline-400 mb-1">
            Filters
          </label>
          <input
            id="session-filters"
            type="text"
            value={filters}
            onChange={(e) => setFilters(e.target.value)}
            placeholder="remote, last 24 hours"
            className="w-full px-3 py-2 rounded bg-pipeline-900 border border-pipeline-600 text-pipeline-100 text-sm placeholder:text-pipeline-600 focus:outline-none focus:border-pipeline-400"
          />
        </div>

        {/* Job Board Search Term Description */}
        <div>
          <label htmlFor="session-search" className="block text-xs text-pipeline-400 mb-1">
            Search Term
          </label>
          <input
            id="session-search"
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="staff data engineer"
            className="w-full px-3 py-2 rounded bg-pipeline-900 border border-pipeline-600 text-pipeline-100 text-sm placeholder:text-pipeline-600 focus:outline-none focus:border-pipeline-400"
          />
        </div>
      </div>

      {error && (
        <p className="mt-2 text-red-400 text-sm">{error}</p>
      )}

      <div className="mt-3 flex gap-2">
        <button
          onClick={handleSubmit}
          disabled={submitting || !searchTerm.trim()}
          className="px-4 py-2 rounded bg-status-apply text-white text-sm font-medium hover:bg-status-apply/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {submitting ? 'Creating…' : 'Create Session'}
        </button>
        <button
          onClick={() => setOpen(false)}
          className="px-4 py-2 rounded text-pipeline-400 text-sm hover:text-pipeline-200 transition-colors"
        >
          Cancel
        </button>
      </div>
    </div>
  )
}
