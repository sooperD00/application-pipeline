/**
 * ResumeCard — display card for a single resume.
 *
 * Shows: label (bold), content preview (first ~3 lines, monospace),
 * created date, Edit and Delete buttons.
 *
 * Display-only — editing happens in ResumeForm (the form switches to
 * edit mode and pre-populates). Delete has an inline confirmation toggle
 * so there's no browser confirm() dialog breaking the all-React pattern.
 */
import { useState } from 'react'

export default function ResumeCard({ resume, onEdit, onDelete }) {
  const [confirmingDelete, setConfirmingDelete] = useState(false)
  const [deleting, setDeleting] = useState(false)

  // Preview: first ~3 lines, truncated. Enough to tell resumes apart at a glance.
  const previewLines = resume.content.split('\n').slice(0, 3).join('\n')
  const hasMore = resume.content.split('\n').length > 3

  async function handleDelete() {
    setDeleting(true)
    try {
      await onDelete(resume.id)
    } catch {
      // parent handles the error; reset our local state
      setDeleting(false)
      setConfirmingDelete(false)
    }
  }

  // Readable date — keep it simple, no timezone gymnastics for MVP
  const created = new Date(resume.created_at).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })

  return (
    <div
      className="p-4 rounded-lg bg-pipeline-800 border border-pipeline-700/50"
      data-testid="resume-card"
    >
      {/* Header row: label + date */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <h3 className="text-sm font-semibold text-pipeline-100 truncate" title={resume.label}>
          {resume.label}
        </h3>
        <span className="text-xs text-pipeline-500 whitespace-nowrap shrink-0">
          {created}
        </span>
      </div>

      {/* Content preview */}
      <pre className="text-xs text-pipeline-400 font-mono whitespace-pre-wrap line-clamp-3 mb-3">
        {previewLines}{hasMore ? '…' : ''}
      </pre>

      {/* Actions */}
      {!confirmingDelete ? (
        <div className="flex gap-2">
          <button
            onClick={() => onEdit(resume)}
            className="px-3 py-1.5 rounded text-xs font-medium text-pipeline-300 bg-pipeline-700 hover:bg-pipeline-600 hover:text-white transition-colors"
          >
            Edit
          </button>
          <button
            onClick={() => setConfirmingDelete(true)}
            className="px-3 py-1.5 rounded text-xs font-medium text-pipeline-400 hover:text-red-400 hover:bg-pipeline-700 transition-colors"
          >
            Delete
          </button>
        </div>
      ) : (
        <div className="flex items-center gap-2">
          <span className="text-xs text-red-400">Delete this resume?</span>
          <button
            onClick={handleDelete}
            disabled={deleting}
            className="px-3 py-1.5 rounded text-xs font-medium text-red-400 bg-red-400/10 hover:bg-red-400/20 disabled:opacity-50 transition-colors"
          >
            {deleting ? 'Deleting…' : 'Yes, delete'}
          </button>
          <button
            onClick={() => setConfirmingDelete(false)}
            disabled={deleting}
            className="px-3 py-1.5 rounded text-xs font-medium text-pipeline-400 hover:text-pipeline-200 transition-colors"
          >
            Cancel
          </button>
        </div>
      )}
    </div>
  )
}
