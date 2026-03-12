import { describe, it, expect, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import App from '../App'

// Mock the API client so SessionLayout doesn't make real fetch calls
// when we navigate to session-scoped routes in tests.
vi.mock('../api/client', () => ({
  listSessions: vi.fn().mockResolvedValue([]),
  getSession: vi.fn().mockResolvedValue({
    id: 'test-session-id',
    user_id: 'test-user-id',
    board: 'LinkedIn',
    filters: 'remote',
    search_term: 'data engineer',
    meta_analysis: null,
    status: 'active',
    created_at: '2026-03-09T00:00:00Z',
    jd_count: 0,
    jds: [],
  }),
  createSession: vi.fn(),
  addJD: vi.fn(),
}))

function renderAt(path) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>
  )
}

describe('App shell — Sprint 8 routing', () => {
  it('renders the nav bar with the app title and all tab labels', () => {
    renderAt('/')
    expect(screen.getByText('ApplicationPipeline')).toBeInTheDocument()

    // All five workflow labels should be visible (ADR-015)
    expect(screen.getByText('Scrape & Analyze')).toBeInTheDocument()
    expect(screen.getByText('Calibrate')).toBeInTheDocument()
    expect(screen.getByText('Review & Enrich')).toBeInTheDocument()
    expect(screen.getByText('Tailoring')).toBeInTheDocument()
    expect(screen.getByText('Resumes')).toBeInTheDocument()
  })

  it('redirects / to /sessions', () => {
    renderAt('/')
    expect(screen.getByRole('heading', { name: /sessions/i })).toBeInTheDocument()
  })

  it('renders Sessions page at /sessions', () => {
    renderAt('/sessions')
    expect(screen.getByRole('heading', { name: /sessions/i })).toBeInTheDocument()
  })

  it('renders Resumes page at /resumes', () => {
    renderAt('/resumes')
    expect(screen.getByRole('heading', { name: /resumes/i })).toBeInTheDocument()
  })

  it('renders 404 page for unknown routes', () => {
    renderAt('/this-does-not-exist')
    expect(screen.getByText('404')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /back to sessions/i })).toBeInTheDocument()
  })

  it('disables session-scoped tabs when no session is active (ADR-015)', () => {
    renderAt('/sessions')
    const nav = screen.getByRole('navigation')

    // Session-scoped tabs should NOT be links when on /sessions (no :id in URL)
    // They render as <span> elements with the disabled tooltip.
    const calibrateTab = within(nav).getByText('Calibrate')
    expect(calibrateTab.tagName).toBe('SPAN')
    expect(calibrateTab).toHaveAttribute(
      'title',
      'Select or create a session to unlock this step.'
    )

    // Resumes should still be a link — it's global
    expect(within(nav).getByRole('link', { name: /resumes/i })).toBeInTheDocument()
  })

  it('enables session-scoped tabs when inside a session', async () => {
    renderAt('/sessions/test-session-id')
    const nav = screen.getByRole('navigation')

    // Session tabs should be real links now
    // (Need to wait for SessionLayout to resolve its fetch)
    const calibrateLink = within(nav).getByRole('link', { name: /calibrate/i })
    expect(calibrateLink).toBeInTheDocument()
    expect(calibrateLink).toHaveAttribute('href', '/sessions/test-session-id/calibrate')
  })
})
