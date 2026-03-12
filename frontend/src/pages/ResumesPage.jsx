/**
 * Tab 5: Resumes — /resumes
 *
 * Global route (not session-scoped). Manages up to 3 resume versions.
 * The backend enforces the cap at 409; this page enforces it visually
 * (disabled button, "3/3" counter) so users don't hit the error path.
 *
 * State lives here. ResumeForm and ResumeCard are display/interaction
 * components — they call back up via onSaved/onEdit/onDelete.
 */
import { useState, useEffect, useCallback } from 'react'
import { listResumes, deleteResume } from '../api/client'
import ResumeCard from '../components/ResumeCard'
import ResumeForm from '../components/ResumeForm'

const MAX_RESUMES = 3

export default function ResumesPage() {
  const [resumes, setResumes] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [editingResume, setEditingResume] = useState(null)

  const fetchResumes = useCallback(async () => {
    try {
      setError(null)
      const data = await listResumes()
      setResumes(data)
    } catch (err) {
      setError(err.detail || err.message || 'Failed to load resumes')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchResumes()
  }, [fetchResumes])

  async function handleDelete(resumeId) {
    await deleteResume(resumeId)
    // If we were editing the resume that just got deleted, clear the form
    if (editingResume?.id === resumeId) {
      setEditingResume(null)
    }
    await fetchResumes()
  }

  function handleEdit(resume) {
    setEditingResume(resume)
  }

  function handleCancelEdit() {
    setEditingResume(null)
  }

  async function handleSaved() {
    setEditingResume(null)
    await fetchResumes()
  }

  const atCap = resumes.length >= MAX_RESUMES
  // Disable the "Add" button when at cap AND not already editing
  // (editing an existing resume doesn't create a new one, so the cap doesn't apply)
  const addDisabled = atCap && !editingResume

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-pipeline-400 text-sm">Loading resumes…</div>
      </div>
    )
  }

  return (
    <div>
      {/* Header with counter */}
      <div className="flex items-baseline justify-between mb-4">
        <h1 className="text-2xl font-semibold">Resumes</h1>
        <span className={`text-sm font-mono ${atCap ? 'text-status-maybe' : 'text-pipeline-400'}`}>
          {resumes.length}/{MAX_RESUMES}
        </span>
      </div>

      {error && (
        <p className="mb-4 text-red-400 text-sm">{error}</p>
      )}

      {/* Form: create or edit */}
      <ResumeForm
        editingResume={editingResume}
        onSaved={handleSaved}
        onCancelEdit={handleCancelEdit}
        disabled={addDisabled}
      />

      {/* Resume cards */}
      {resumes.length > 0 && (
        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {resumes.map((resume) => (
            <ResumeCard
              key={resume.id}
              resume={resume}
              onEdit={handleEdit}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      {resumes.length === 0 && (
        <p className="mt-8 text-pipeline-500 text-sm">
          No resumes yet. Add your first resume above — you'll need at least one before analysis or tailoring can run.
        </p>
      )}
    </div>
  )
}
