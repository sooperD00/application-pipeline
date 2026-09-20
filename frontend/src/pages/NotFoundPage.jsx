/**
 * 404 catch-all — rendered by the `*` route in App.jsx.
 *
 * Friendly nudge back to the sessions list. Nothing fancy.
 */
import { Link } from 'react-router-dom'

export default function NotFoundPage() {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <h1 className="text-4xl font-bold text-pipeline-400 mb-2">404</h1>
      <p className="text-pipeline-500 mb-6">
        This page doesn't exist — or hasn't been built yet.
      </p>
      {/* [SPRINT-77f2e3-CLEANUP] When /tracking becomes the index route (ADR-016), this
          link navigates to "/" and lets the router decide, or uses navigate(-1) to send users
          back where they came from. Frontend polish owns the copy either way. */}
      <Link
        to="/sessions"
        className="px-4 py-2 rounded-lg bg-pipeline-700 text-white text-sm font-medium hover:bg-pipeline-600 transition-colors"
      >
        Back to Sessions
      </Link>
    </div>
  )
}
