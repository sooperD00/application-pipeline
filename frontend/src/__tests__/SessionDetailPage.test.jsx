import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import SessionLayout from '../pages/SessionLayout'
import SessionDetailPage from '../pages/SessionDetailPage'
import * as client from '../api/client'

// Mock the entire client module — we control every API response
vi.mock('../api/client')

// ── Fixtures ────────────────────────────────────────────────────────────────

const SESSION_ID = '00000000-0000-0000-0000-000000000001'

const existingJDs = [
  {
    id: 'jd-aaa',
    session_id: SESSION_ID,
    number: 1,
    company: 'Acme Corp',
    role: 'Staff Data Engineer',
    status: 'pending',
    status_source: 'ai',
    cleaned_text: 'JD 1 text',
    analysis_text: null,
    compensation: null,
    employee_count: null,
    link: null,
    cover_letter_requested: false,
    flagged_for_review: false,
    created_at: '2026-03-09T00:00:00Z',
  },
  {
    id: 'jd-bbb',
    session_id: SESSION_ID,
    number: 2,
    company: 'Widgets Inc',
    role: 'Senior Backend Engineer',
    status: 'pending',
    status_source: 'ai',
    cleaned_text: 'JD 2 text',
    analysis_text: null,
    compensation: null,
    employee_count: null,
    link: null,
    cover_letter_requested: false,
    flagged_for_review: false,
    created_at: '2026-03-09T00:01:00Z',
  },
]

const newJD = {
  id: 'jd-ccc',
  session_id: SESSION_ID,
  number: 3,
  company: 'DataCo',
  role: 'Platform Engineer',
  status: 'pending',
  status_source: 'ai',
  cleaned_text: 'JD 3 text here',
  analysis_text: null,
  compensation: null,
  employee_count: null,
  link: null,
  cover_letter_requested: false,
  flagged_for_review: false,
  created_at: '2026-03-09T00:02:00Z',
}

function makeSessionResponse(jds) {
  return {
    id: SESSION_ID,
    user_id: 'user-001',
    board: 'LinkedIn',
    filters: 'remote, last 24 hours',
    search_term: 'staff data engineer',
    meta_analysis: null,
    status: 'active',
    created_at: '2026-03-09T00:00:00Z',
    jd_count: jds.length,
    jds,
  }
}

function renderSessionDetail() {
  return render(
    <MemoryRouter initialEntries={[`/sessions/${SESSION_ID}`]}>
      <Routes>
        <Route path="/sessions/:id" element={<SessionLayout />}>
          <Route index element={<SessionDetailPage />} />
        </Route>
      </Routes>
    </MemoryRouter>
  )
}

// ── Tests ────────────────────────────────────────────────────────────────────

describe('SessionDetailPage — JD paste flow', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('renders existing JDs as cards after loading', async () => {
    client.getSession.mockResolvedValue(makeSessionResponse(existingJDs))

    renderSessionDetail()

    // Wait for loading to finish and cards to appear
    await waitFor(() => {
      expect(screen.getByText('Acme Corp')).toBeInTheDocument()
    })

    expect(screen.getByText('Widgets Inc')).toBeInTheDocument()
    expect(screen.getByText('Staff Data Engineer')).toBeInTheDocument()
    expect(screen.getByText('Senior Backend Engineer')).toBeInTheDocument()

    // Both cards should show number badges
    expect(screen.getByText('1')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
  })

  it('shows session metadata in the header', async () => {
    client.getSession.mockResolvedValue(makeSessionResponse(existingJDs))

    renderSessionDetail()

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /staff data engineer/i })).toBeInTheDocument()
    })
    expect(screen.getByText(/LinkedIn · remote, last 24 hours/)).toBeInTheDocument()
  })

  it('paste JD → submit → new card appears', async () => {
    const user = userEvent.setup()

    // First fetch: 2 existing JDs
    // After addJD + refreshSession: 3 JDs
    client.getSession
      .mockResolvedValueOnce(makeSessionResponse(existingJDs))
      .mockResolvedValueOnce(makeSessionResponse([...existingJDs, newJD]))

    client.addJD.mockResolvedValue(newJD)

    renderSessionDetail()

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('Acme Corp')).toBeInTheDocument()
    })

    // Type into the paste textarea
    const textarea = screen.getByPlaceholderText(/paste the full job description/i)
    await user.type(textarea, 'JD 3 text here')

    // Optionally fill company
    const companyInput = screen.getByPlaceholderText('Acme Corp')
    await user.type(companyInput, 'DataCo')

    // Submit
    const addButton = screen.getByRole('button', { name: /add jd/i })
    await user.click(addButton)

    // addJD should have been called with correct args
    expect(client.addJD).toHaveBeenCalledWith(SESSION_ID, {
      raw_text: 'JD 3 text here',
      company: 'DataCo',
      role: '',
    })

    // After refresh, the new card appears
    await waitFor(() => {
      expect(screen.getByText('DataCo')).toBeInTheDocument()
    })
    expect(screen.getByText('Platform Engineer')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
  })

  it('shows empty state when session has no JDs', async () => {
    client.getSession.mockResolvedValue(makeSessionResponse([]))

    renderSessionDetail()

    await waitFor(() => {
      expect(screen.getByText(/no jds yet/i)).toBeInTheDocument()
    })
  })
})


// ── Sprint 10: Analyze button ────────────────────────────────────────────────

describe('SessionDetailPage — Analyze button', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('renders Analyze button when JDs exist', async () => {
    client.getSession.mockResolvedValue(makeSessionResponse(existingJDs))

    renderSessionDetail()

    await waitFor(() => {
      expect(screen.getByTestId('analyze-button')).toBeInTheDocument()
    })
    expect(screen.getByTestId('analyze-button')).toHaveTextContent('Analyze')
    expect(screen.getByTestId('analyze-button')).not.toBeDisabled()
  })

  it('does not render Analyze button when no JDs exist', async () => {
    client.getSession.mockResolvedValue(makeSessionResponse([]))

    renderSessionDetail()

    await waitFor(() => {
      expect(screen.getByText(/no jds yet/i)).toBeInTheDocument()
    })
    expect(screen.queryByTestId('analyze-button')).not.toBeInTheDocument()
  })

  it('disables Analyze button when session status is analyzing', async () => {
    const analyzingSession = makeSessionResponse(existingJDs)
    analyzingSession.status = 'analyzing'
    client.getSession.mockResolvedValue(analyzingSession)

    renderSessionDetail()

    await waitFor(() => {
      expect(screen.getByTestId('analyze-button')).toBeInTheDocument()
    })
    expect(screen.getByTestId('analyze-button')).toBeDisabled()
  })

  it('shows warning banner with link to /resumes on 422 no-resumes error', async () => {
    const user = userEvent.setup()
    client.getSession.mockResolvedValue(makeSessionResponse(existingJDs))

    // analyzeSession throws an error shaped like ApiError (status + detail)
    client.analyzeSession.mockRejectedValue(
      Object.assign(new Error('No resumes'), {
        status: 422,
        detail: 'No resumes found. Create at least one resume before analyzing.',
      })
    )

    renderSessionDetail()

    await waitFor(() => {
      expect(screen.getByTestId('analyze-button')).toBeInTheDocument()
    })

    await user.click(screen.getByTestId('analyze-button'))

    await waitFor(() => {
      expect(screen.getByTestId('warning-banner')).toBeInTheDocument()
    })
    expect(screen.getByText(/no resumes found/i)).toBeInTheDocument()
    expect(screen.getByText(/go to resumes/i)).toBeInTheDocument()
  })

  it('shows warning banner on 409 conflict (analysis already running)', async () => {
    const user = userEvent.setup()
    client.getSession.mockResolvedValue(makeSessionResponse(existingJDs))

    client.analyzeSession.mockRejectedValue(
      Object.assign(new Error('Conflict'), {
        status: 409,
        detail: 'Analysis already in progress for this session.',
      })
    )

    renderSessionDetail()

    await waitFor(() => {
      expect(screen.getByTestId('analyze-button')).toBeInTheDocument()
    })

    await user.click(screen.getByTestId('analyze-button'))

    await waitFor(() => {
      expect(screen.getByTestId('warning-banner')).toBeInTheDocument()
    })
    expect(screen.getByText(/already in progress/i)).toBeInTheDocument()
  })

  it('shows red error banner with retry on unexpected errors', async () => {
    const user = userEvent.setup()
    client.getSession.mockResolvedValue(makeSessionResponse(existingJDs))

    client.analyzeSession.mockRejectedValue(
      Object.assign(new Error('Server error'), {
        status: 500,
        detail: 'Internal server error',
      })
    )

    renderSessionDetail()

    await waitFor(() => {
      expect(screen.getByTestId('analyze-button')).toBeInTheDocument()
    })

    await user.click(screen.getByTestId('analyze-button'))

    await waitFor(() => {
      expect(screen.getByTestId('error-banner')).toBeInTheDocument()
    })
    expect(screen.getByText(/internal server error/i)).toBeInTheDocument()
    // Retry button should be present
    expect(screen.getByText('Retry')).toBeInTheDocument()
  })
})

