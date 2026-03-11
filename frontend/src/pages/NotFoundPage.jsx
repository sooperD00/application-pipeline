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
      {/* TODO (post-Phase 0): When /tracking becomes the index route,
          this link should navigate to "/" and let the router decide,
          or use navigate(-1) to send users where they came from. */}
      <Link
        to="/sessions"
        className="px-4 py-2 rounded-lg bg-pipeline-700 text-white text-sm font-medium hover:bg-pipeline-600 transition-colors"
      >
        Back to Sessions
      </Link>
    </div>
  )
}
