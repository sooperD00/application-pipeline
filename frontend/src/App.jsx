/**
 * App.jsx
 * 
 * App owns chrome → Layout owns data → Page owns UI.
 * 
 */
import { Routes, Route, NavLink, Navigate, useMatch } from 'react-router-dom'
import SessionsPage from './pages/SessionsPage'
import SessionLayout from './pages/SessionLayout'
import SessionDetailPage from './pages/SessionDetailPage'
import CalibratePage from './pages/CalibratePage'
import ReviewPage from './pages/ReviewPage'
import TailoringPage from './pages/TailoringPage'
import ResumesPage from './pages/ResumesPage'
import NotFoundPage from './pages/NotFoundPage'

/**
 * ADR-015: All five tabs always visible. Session-scoped tabs (Calibrate,
 * Review, Tailoring) are grayed/disabled when no session is active.
 * "The tab bar *is* the product story."
 */

function NavBar() {
  // Matches any /sessions/:id or /sessions/:id/subpath route
  /* useMatch here is a structural decision - the NavBar isn't inside the session layout
   * so it can't use useSessionContext(). Instead it reads the URL and "uses" any "match"
   * to /sessions/:id/. The deliberate choice here is that the navbar needs to know about sessions
   * but doesn't own them.
  */
  const sessionMatch = useMatch('/sessions/:id/*')
  const sessionId = sessionMatch?.params?.id

  // Tabs 1–4 are session-scoped; Resumes is global
  const sessionTabs = [
    { path: '',          label: 'Scrape & Analyze' },
    { path: '/calibrate', label: 'Calibrate' },
    { path: '/review',   label: 'Review & Enrich' },
    { path: '/tailor',   label: 'Tailoring' },
  ]

  return (
    <nav className="bg-pipeline-900 text-pipeline-100 border-b border-pipeline-700/50">
      <div className="max-w-7xl mx-auto px-4 flex items-center h-14 gap-8">
        <NavLink
          to="/sessions"
          className="font-semibold text-lg tracking-tight text-white shrink-0 hover:text-pipeline-300 transition-colors"
        >
          ApplicationPipeline
        </NavLink>

        <div className="flex gap-1 overflow-x-auto">
          {sessionTabs.map(({ path, label }) => {
            if (sessionId) {
              const to = `/sessions/${sessionId}${path}`
              return (
                <NavLink
                  key={path}
                  to={to}
                  end={path === ''} // for UX: only highlight this tab when the URL is exactly /sessions/:id
                  className={({ isActive }) =>
                    `px-3 py-2 rounded text-sm font-medium whitespace-nowrap transition-colors ${
                      isActive
                        ? 'bg-pipeline-700 text-white'
                        : 'text-pipeline-300 hover:text-white hover:bg-pipeline-800'
                    }`
                  }
                >
                  {label}
                </NavLink>
              )
            }

            // No active session — disabled tab (ADR-015)
            return (
              <span
                key={path}
                title="Select or create a session to unlock this step."
                className="px-3 py-2 rounded text-sm font-medium whitespace-nowrap text-pipeline-600 cursor-not-allowed"
              >
                {label}
              </span>
            )
          })}

          {/* Resumes — always active, global route */}
          <NavLink
            to="/resumes"
            className={({ isActive }) =>
              `px-3 py-2 rounded text-sm font-medium whitespace-nowrap transition-colors ${
                isActive
                  ? 'bg-pipeline-700 text-white'
                  : 'text-pipeline-300 hover:text-white hover:bg-pipeline-800'
              }`
            }
          >
            Resumes
          </NavLink>
        </div>
      </div>
    </nav>
  )
}

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <NavBar />
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-6">
        <Routes>
          {/* replace prevents back-button loop between / and /sessions */}
          <Route path="/" element={<Navigate to="/sessions" replace />} /> 
          <Route path="/sessions" element={<SessionsPage />} />

          {/* Session-scoped nested routes */}
          <Route path="/sessions/:id" element={<SessionLayout />}>
            <Route index element={<SessionDetailPage />} />
            <Route path="calibrate" element={<CalibratePage />} />
            <Route path="review" element={<ReviewPage />} />
            <Route path="tailor" element={<TailoringPage />} />
          </Route>

          <Route path="/resumes" element={<ResumesPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </main>
    </div>
  )
}
