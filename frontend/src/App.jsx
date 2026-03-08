import { Routes, Route, NavLink, Navigate } from 'react-router-dom'
import SessionsPage from './pages/SessionsPage'
import CalibratePage from './pages/CalibratePage'
import ReviewPage from './pages/ReviewPage'
import TailoringPage from './pages/TailoringPage'
import ResumesPage from './pages/ResumesPage'

const navItems = [
  { to: '/sessions', label: 'Scrape & Analyze' },
  { to: '/calibrate', label: 'Calibrate' },
  { to: '/review', label: 'Review & Enrich' },
  { to: '/tailoring', label: 'Tailoring' },
  { to: '/resumes', label: 'Resumes' },
]

function NavBar() {
  return (
    <nav className="bg-pipeline-900 text-pipeline-100">
      <div className="max-w-7xl mx-auto px-4 flex items-center h-14 gap-8">
        <span className="font-semibold text-lg tracking-tight text-white shrink-0">
          ApplicationPipeline
        </span>
        <div className="flex gap-1 overflow-x-auto">
          {navItems.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
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
          ))}
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
          <Route path="/" element={<Navigate to="/sessions" replace />} />
          <Route path="/sessions" element={<SessionsPage />} />
          <Route path="/calibrate" element={<CalibratePage />} />
          <Route path="/review" element={<ReviewPage />} />
          <Route path="/tailoring" element={<TailoringPage />} />
          <Route path="/resumes" element={<ResumesPage />} />
        </Routes>
      </main>
    </div>
  )
}
