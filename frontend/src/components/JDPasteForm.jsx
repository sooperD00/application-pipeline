/**
 * JDPasteForm — paste a job description into a session.
 *
 * Main field: raw_text textarea (required).
 * Optional: company and role (helps label cards before analysis extracts them).
 * The backend auto-cleans text and assigns the JD number.
 *
 * After submit, calls onAdded() so the parent refreshes the card grid.
 * The 25-JD cap is enforced server-side (409 response).
 */
import { useState } from 'react'
import { addJD } from '../api/client'

export default function JDPasteForm({ sessionId, onAdded }) {  // importable by other files
  // const [ value, setter] = default
  const [rawText, setRawText] = useState('')  // destructuring (JS's array destructuring)
  const [company, setCompany] = useState('')
  const [role, setRole] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit() {
    if (!rawText.trim()) return

    setSubmitting(true)
    setError(null)
    try {
      await addJD(sessionId, {
        raw_text: rawText,
        company: company.trim(),
        role: role.trim(),
      })
      // Clear the paste area; keep company/role in case the user is
      // pasting from the same board listing (same company, different role)
      setRawText('')
      setError(null)
      await onAdded()
    } catch (err) {
      setError(err.detail || err.message || 'Failed to add JD')
    } finally {
      setSubmitting(false)
    }
  }

  /* Submit shortcut: currently Enter (Shift+Enter for newline).
     Strong arguments both ways:
     - Enter-to-submit: faster for power users pasting 25+ JDs/session,
       saves wrist strain on Ctrl/Cmd over repetitive workflows
     - Cmd+Enter-to-submit: safer for multi-line editing, prevents
       accidental submits
     TODO: Make this a user-toggleable preference (small toggle in the
     form footer). Both implementations below — swap active/commented. */

/*   // Ctrl+Enter / Cmd+Enter to submit from the textarea
  function handleKeyDown(e) {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      handleSubmit()
    }
  } */

  // Enter to submit from the textarea (dev preference ships in Phase 0 ;) )
  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()  // stop the default newline
      handleSubmit()
    }
    // Shift+Enter falls through to default behavior (newline)
  }

  /* TODO: Auto-populate company/role from first lines of pasted text.
   Job boards typically paste as some combination of: 
    [junk] \n Company \n Role \n [junk].
   Quick win to paste the 1st to lines before Sprint 10's Claude extraction. 
   Better win later to do some light logic processing of the first 5 lines,
   e.g. LinkedIn:
    Publisher Services, Inc logo
    Publisher Services, Inc  <------------- Company
    Share
    Show more options
    Advertising and Optimization Specialist   <------------- Role
    Minneapolis, MN · 59 minutes ago · 1 applicant
    Promoted by hirer · No response insights available yet
  e.g. WTTJ:
    Home
    Jobs
    Companies
    Inbox

    You
    Led by women
    Companies founded or currently led by women.

    Staff Data Engineer, Vanta   <-------------- Role, Company
    (optional sub-role like "Platform")
    $213-251k
  and actually, you have hints from the user who enters the job board as metadata / session name tag
    */

  return (
    <div className="p-4 rounded-lg bg-pipeline-800 border border-pipeline-700/50">

      {/* Paste a Job Description */}
      <h2 className="text-sm font-medium text-pipeline-300 mb-3">Paste a Job Description</h2>

      <textarea
        value={rawText}
        onChange={(e) => setRawText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Paste the full job description here…"
        rows={6}
        className="w-full px-3 py-2 rounded bg-pipeline-900 border border-pipeline-600 text-pipeline-100 text-sm placeholder:text-pipeline-600 focus:outline-none focus:border-pipeline-400 resize-y font-mono"
      />

      {/* Optional Company/Role Explicit Specification by the User */}
      {/* - below the main JD paste box */}
      <div className="mt-2 grid grid-cols-2 gap-3">
        {/* Company */}
        <div>
          <label htmlFor="jd-company" className="block text-xs text-pipeline-400 mb-1">
            Company (optional)
          </label>
          <input
            id="jd-company"
            type="text"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            placeholder="Gargoyle Labs"
            className="w-full px-3 py-2 rounded bg-pipeline-900 border border-pipeline-600 text-pipeline-100 text-sm placeholder:text-pipeline-600 focus:outline-none focus:border-pipeline-400"
          />
        </div>

        {/* Role */}
        <div>
          <label htmlFor="jd-role" className="block text-xs text-pipeline-400 mb-1">
            Role (optional)
          </label>
          <input
            id="jd-role"
            type="text"
            value={role}
            onChange={(e) => setRole(e.target.value)}
            placeholder="Independent Developer"
            className="w-full px-3 py-2 rounded bg-pipeline-900 border border-pipeline-600 text-pipeline-100 text-sm placeholder:text-pipeline-600 focus:outline-none focus:border-pipeline-400"
          />
        </div>
      </div>
      {/* TODO (Sprint 10+): Claude analysis will auto-extract company/role from raw_text.
          These fields become pre-populated + editable, not manual entry. Consider visually de-emphasizing. */}

      {/* error */}
      {error && (
        <p className="mt-2 text-red-400 text-sm">{error}</p>
      )}

      {/* Handle Submit */}
      <div className="mt-3 flex items-center gap-3">
        <button
          onClick={handleSubmit}
          disabled={submitting || !rawText.trim()}  // button grayed out & unclickable (visual feedback) when mid-submit or empty/whitespace - no double-clicks firing API calls
          className="px-4 py-2 rounded bg-pipeline-600 text-white text-sm font-medium hover:bg-pipeline-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {/* button text changes while the API call is in flight so the user knows something's happening */}
          {submitting ? 'Adding…' : 'Add JD'}

        </button>
        <span className="text-xs text-pipeline-500">
          Enter to submit
        </span>
      </div>
    </div>
  )
}
