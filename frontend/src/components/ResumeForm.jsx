/**
 * ResumeForm — create or edit a resume.
 *
 * Dual-mode form:
 *   - Create: editingResume is null. Save calls createResume().
 *   - Edit:   editingResume is a resume object. Save calls updateResume().
 *
 * Follows the SessionCreateForm reveal pattern: starts as a button,
 * click opens the panel. When the parent sets editingResume, the form
 * opens pre-populated. Cancel clears the editing state.
 *
 * Enter-to-submit on the label field only (not the textarea — resume
 * text is multi-line, so Enter should insert a newline there).
 */
import { useState, useEffect } from 'react'
import { createResume, updateResume } from '../api/client'

export default function ResumeForm({ editingResume, onSaved, onCancelEdit, disabled }) {
  const [open, setOpen] = useState(false)
  const [label, setLabel] = useState('')
  const [content, setContent] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const isEditing = editingResume !== null

  // When editingResume changes, open and populate (or reset)
  useEffect(() => {
    if (editingResume) {
      setLabel(editingResume.label)
      setContent(editingResume.content)
      setOpen(true)
      setError(null)
    }
  }, [editingResume])

  function resetForm() {
    setLabel('')
    setContent('')
    setError(null)
  }

  function handleCancel() {
    resetForm()
    setOpen(false)
    if (isEditing) onCancelEdit()
  }

  async function handleSubmit() {
    if (!label.trim() || !content.trim()) return

    setSubmitting(true)
    setError(null)
    try {
      if (isEditing) {
        await updateResume(editingResume.id, {
          label: label.trim(),
          content: content.trim(),
        })
      } else {
        await createResume({
          label: label.trim(),
          content: content.trim(),
        })
      }
      resetForm()
      setOpen(false)
      if (isEditing) onCancelEdit()
      await onSaved()
    } catch (err) {
      setError(err.detail || err.message || 'Failed to save resume')
    } finally {
      setSubmitting(false)
    }
  }

  // Enter-to-submit on the label field only
  function handleLabelKeyDown(e) {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleSubmit()
    }
  }

  // Collapsed state: just the button
  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        disabled={disabled}
        className="px-4 py-2 rounded-lg bg-pipeline-700 text-white text-sm font-medium hover:bg-pipeline-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        + Add Resume
      </button>
    )
  }

  return (
    <div className="p-4 rounded-lg bg-pipeline-800 border border-pipeline-700/50">
      <h2 className="text-sm font-medium text-pipeline-300 mb-3">
        {isEditing ? `Editing: ${editingResume.label}` : 'New Resume'}
      </h2>

      {/* Label */}
      <div className="mb-3">
        <label htmlFor="resume-label" className="block text-xs text-pipeline-400 mb-1">
          Label
        </label>
        <input
          id="resume-label"
          type="text"
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          onKeyDown={handleLabelKeyDown}
          placeholder='e.g. "Technical", "Leadership", "Platform"'
          className="w-full px-3 py-2 rounded bg-pipeline-900 border border-pipeline-600 text-pipeline-100 text-sm placeholder:text-pipeline-600 focus:outline-none focus:border-pipeline-400"
        />
      </div>

      {/* Content (resume text) */}
      <div className="mb-3">
        <label htmlFor="resume-content" className="block text-xs text-pipeline-400 mb-1">
          Resume Text
        </label>
        <textarea
          id="resume-content"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Paste your full resume text here…"
          rows={12}
          className="w-full px-3 py-2 rounded bg-pipeline-900 border border-pipeline-600 text-pipeline-100 text-sm placeholder:text-pipeline-600 focus:outline-none focus:border-pipeline-400 resize-y font-mono"
        />
      </div>

      {error && (
        <p className="mt-2 text-red-400 text-sm">{error}</p>
      )}

      <div className="mt-3 flex items-center gap-3">
        <button
          onClick={handleSubmit}
          disabled={submitting || !label.trim() || !content.trim()}
          className="px-4 py-2 rounded bg-status-apply text-white text-sm font-medium hover:bg-status-apply/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {submitting
            ? 'Saving…'
            : isEditing ? 'Save Changes' : 'Save Resume'}
        </button>
        <button
          onClick={handleCancel}
          disabled={submitting}
          className="px-4 py-2 rounded text-pipeline-400 text-sm hover:text-pipeline-200 transition-colors"
        >
          Cancel
        </button>
        {!isEditing && (
          <span className="text-xs text-pipeline-500">
            Enter on label to submit
          </span>
        )}
      </div>
    </div>
  )
}
