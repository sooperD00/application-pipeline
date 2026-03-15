import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import SessionLayout from '../pages/SessionLayout'
import TailoringPage from '../pages/TailoringPage'
import * as client from '../api/client'

// Mock the entire client module — we control every API response
vi.mock('../api/client')

// ── Fixtures ────────────────────────────────────────────────────────────────

const SESSION_ID = '00000000-0000-0000-0000-000000000001'

const applyJDs = [
  {
    id: 'jd-aaa',
    session_id: SESSION_ID,
    number: 1,
    company: 'Acme Corp',
    role: 'Staff Data Engineer',
    status: 'apply',
    status_source: 'ai',
    cleaned_text: 'JD 1 text',
    analysis_text: 'Strong fit.',
    compensation: '$180k',
    employee_count: null,
    link: 'https://example.com',
    cover_letter_requested: true,
    flagged_for_review: false,
    created_at: '2026-03-09T00:00:00Z',
  },
  {
    id: 'jd-bbb',
    session_id: SESSION_ID,
    number: 3,
    company: 'Widgets Inc',
    role: 'Senior Backend Engineer',
    status: 'apply',
    status_source: 'ai',
    cleaned_text: 'JD 3 text',
    analysis_text: 'Good match.',
    compensation: null,
    employee_count: null,
    link: null,
    cover_letter_requested: false,
    flagged_for_review: false,
    created_at: '2026-03-09T00:02:00Z',
  },
]

// explicitly test that non-apply JDs are excluded
const noJD = {
  id: 'jd-ccc',
  session_id: SESSION_ID,
  number: 2,
  company: 'Other Inc',
  role: 'Junior Dev',
  status: 'no',  // status: 'no' (negative test)
  status_source: 'ai',
  cleaned_text: 'JD 2 text',
  analysis_text: null,
  compensation: null,
  employee_count: null,
  link: null,
  cover_letter_requested: false,
  flagged_for_review: false,
  created_at: '2026-03-09T00:01:00Z',
}

function makeSessionResponse(jds) {
  return {
    id: SESSION_ID,
    user_id: 'user-001',
    board: 'LinkedIn',
    filters: 'remote, last 24 hours',
    search_term: 'staff data engineer',
    meta_analysis: null,
    status: 'complete',
    created_at: '2026-03-09T00:00:00Z',
    jd_count: jds.length,
    jds,
  }
}

const readyJob = {
  id: 'job-111',
  jd_id: 'jd-aaa',
  resume_id: 'resume-aaa',
  status: 'ready',
  output_resume: 'Nicole L. Rowsey\nStaff engineer...',
  output_cover_letter: 'Dear Hiring Manager...',
  output_app_answers: [{ question: 'Why us?', answer: 'Mission.' }],
  has_docx: true,
  model_used: 'claude-opus-4-6',
  created_at: '2026-03-10T00:00:00Z',
  completed_at: '2026-03-10T00:05:00Z',
  company: 'Acme Corp',
  role: 'Staff Data Engineer',
  jd_number: 1,
}

const failedJob = {
  id: 'job-222',
  jd_id: 'jd-bbb',
  resume_id: 'resume-aaa',
  status: 'failed',
  output_resume: null,
  output_cover_letter: null,
  output_app_answers: null,
  has_docx: false,
  model_used: 'claude-opus-4-6',
  created_at: '2026-03-10T00:00:00Z',
  completed_at: null,
  company: 'Widgets Inc',
  role: 'Senior Backend Engineer',
  jd_number: 3,
}

const queuedJob = {
  ...readyJob,
  id: 'job-333',
  status: 'queued',
  output_resume: null,
  output_cover_letter: null,
  output_app_answers: null,
  has_docx: false,
  completed_at: null,
}

const nullResumeJob = {
  ...readyJob,
  id: 'job-444',
  resume_id: null,
}

function renderTailoringPage() {
  return render(
    <MemoryRouter initialEntries={[`/sessions/${SESSION_ID}/tailor`]}>
      <Routes>
        <Route path="/sessions/:id" element={<SessionLayout />}>
          <Route path="tailor" element={<TailoringPage />} />
        </Route>
      </Routes>
    </MemoryRouter>
  )
}

// ── Tests ────────────────────────────────────────────────────────────────────

describe('TailoringPage', () => {
  beforeEach(() => {
    // prevent mock leakage between tests
    vi.restoreAllMocks()
    
    // Suppress setInterval from polling in tests
    // so tests don't flake from real setTimeout races
    vi.useFakeTimers({ shouldAdvanceTime: false })  
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('renders ready job cards with download buttons', async () => {
    client.getSession.mockResolvedValue(makeSessionResponse([...applyJDs, noJD]))
    client.listSessionTailoringJobs.mockResolvedValue([readyJob])

    renderTailoringPage()

    await waitFor(() => {
      expect(screen.getByText('Acme Corp')).toBeInTheDocument()
    })

    // Status badge
    expect(screen.getByText('Ready')).toBeInTheDocument()

    // Output indicators
    expect(screen.getByTestId('output-indicators')).toHaveTextContent('Resume ✓')
    expect(screen.getByTestId('output-indicators')).toHaveTextContent('Cover letter ✓')
    expect(screen.getByTestId('output-indicators')).toHaveTextContent('App answers ✓')

    // Download buttons visible
    expect(screen.getByTestId('download-docx')).toBeInTheDocument()
    expect(screen.getByTestId('download-package')).toBeInTheDocument()
  })

  it('download docx button calls API with correct job and JD ids', async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })

    client.getSession.mockResolvedValue(makeSessionResponse(applyJDs))
    client.listSessionTailoringJobs.mockResolvedValue([readyJob])
    client.downloadTailoringDocx.mockResolvedValue(new Blob(['test'], { type: 'application/octet-stream' }))

    renderTailoringPage()

    await waitFor(() => {
      expect(screen.getByTestId('download-docx')).toBeInTheDocument()
    })

    await user.click(screen.getByTestId('download-docx'))

    expect(client.downloadTailoringDocx).toHaveBeenCalledWith('jd-aaa', 'job-111')
  })

  it('renders failed job with retry button', async () => {
    client.getSession.mockResolvedValue(makeSessionResponse([...applyJDs, noJD]))
    client.listSessionTailoringJobs.mockResolvedValue([failedJob])

    renderTailoringPage()

    await waitFor(() => {
      expect(screen.getByText('Widgets Inc')).toBeInTheDocument()
    })

    expect(screen.getByText('Failed')).toBeInTheDocument()
    expect(screen.getByTestId('retry-button')).toBeInTheDocument()

    // No download buttons on failed jobs
    expect(screen.queryByTestId('download-docx')).not.toBeInTheDocument()
    expect(screen.queryByTestId('download-package')).not.toBeInTheDocument()
  })

  it('shows "not started" cards for apply JDs without jobs', async () => {
    client.getSession.mockResolvedValue(makeSessionResponse([...applyJDs, noJD]))
    client.listSessionTailoringJobs.mockResolvedValue([readyJob]) // only jd-aaa has a job

    renderTailoringPage()

    await waitFor(() => {
      expect(screen.getByText('Acme Corp')).toBeInTheDocument()
    })

    // jd-bbb (Widgets Inc) is apply-status but has no job → "not started" card
    const notStartedCards = screen.getAllByTestId('not-started-card')
    expect(notStartedCards).toHaveLength(1)
    expect(screen.getByText('Widgets Inc')).toBeInTheDocument()

    // "no" status JD (Other Inc) should NOT appear
    expect(screen.queryByText('Other Inc')).not.toBeInTheDocument()
  })

  it('handles resume_id: null gracefully', async () => {
    client.getSession.mockResolvedValue(makeSessionResponse(applyJDs))
    client.listSessionTailoringJobs.mockResolvedValue([nullResumeJob])

    renderTailoringPage()

    await waitFor(() => {
      expect(screen.getByText('Acme Corp')).toBeInTheDocument()
    })

    expect(screen.getByText(/source resume deleted/i)).toBeInTheDocument()
    // Downloads should still work
    expect(screen.getByTestId('download-docx')).toBeInTheDocument()
    expect(screen.getByTestId('download-package')).toBeInTheDocument()
  })

  it('queued job shows spinner, no download buttons', async () => {
    client.getSession.mockResolvedValue(makeSessionResponse(applyJDs))
    client.listSessionTailoringJobs.mockResolvedValue([queuedJob])

    renderTailoringPage()

    await waitFor(() => {
      expect(screen.getByText('Queued')).toBeInTheDocument()
    })

    expect(screen.queryByTestId('download-docx')).not.toBeInTheDocument()
    expect(screen.queryByTestId('download-package')).not.toBeInTheDocument()
  })

  it('batch tailor button calls API', async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })

    client.getSession.mockResolvedValue(makeSessionResponse(applyJDs))
    client.listSessionTailoringJobs.mockResolvedValue([])
    client.batchTailor.mockResolvedValue({ jobs: [], jd_count: 2 })

    renderTailoringPage()

    await waitFor(() => {
      expect(screen.getByTestId('batch-tailor-button')).toBeInTheDocument()
    })

    await user.click(screen.getByTestId('batch-tailor-button'))

    expect(client.batchTailor).toHaveBeenCalledWith(SESSION_ID)
  })

  it('single JD tailor button calls API with correct JD id', async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })

    client.getSession.mockResolvedValue(makeSessionResponse(applyJDs))
    client.listSessionTailoringJobs.mockResolvedValue([]) // no jobs yet → all show "not started"
    client.createTailoringJob.mockResolvedValue(queuedJob)

    renderTailoringPage()

    await waitFor(() => {
      expect(screen.getAllByTestId('not-started-card')).toHaveLength(2)
    })

    // Click the first "Tailor" button (jd-aaa, sorted by number)
    const tailorButtons = screen.getAllByTestId('tailor-single')
    await user.click(tailorButtons[0])

    expect(client.createTailoringJob).toHaveBeenCalledWith('jd-aaa')
  })

  it('retry button on failed job calls API with correct JD id', async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })

    client.getSession.mockResolvedValue(makeSessionResponse(applyJDs))
    client.listSessionTailoringJobs.mockResolvedValue([failedJob])
    client.createTailoringJob.mockResolvedValue(queuedJob)

    renderTailoringPage()

    await waitFor(() => {
      expect(screen.getByTestId('retry-button')).toBeInTheDocument()
    })

    await user.click(screen.getByTestId('retry-button'))

    expect(client.createTailoringJob).toHaveBeenCalledWith('jd-bbb')
  })

  it('shows error banner when tailoring jobs fail to load', async () => {
    client.getSession.mockResolvedValue(makeSessionResponse(applyJDs))
    client.listSessionTailoringJobs.mockRejectedValue(new Error('Network timeout'))

    renderTailoringPage()

    await waitFor(() => {
      expect(screen.getByTestId('error-banner')).toBeInTheDocument()
    })

    expect(screen.getByTestId('error-banner')).toHaveTextContent('Network timeout')
  })

  it('shows empty state when no apply JDs and no jobs', async () => {
    client.getSession.mockResolvedValue(makeSessionResponse([noJD]))
    client.listSessionTailoringJobs.mockResolvedValue([])

    renderTailoringPage()

    await waitFor(() => {
      expect(screen.getByText(/no apply-status jds/i)).toBeInTheDocument()
    })
  })

  it('shows summary chips', async () => {
    client.getSession.mockResolvedValue(makeSessionResponse(applyJDs))
    client.listSessionTailoringJobs.mockResolvedValue([readyJob, failedJob])

    renderTailoringPage()

    await waitFor(() => {
      expect(screen.getByTestId('tailoring-summary')).toBeInTheDocument()
    })

    expect(screen.getByTestId('tailoring-summary')).toHaveTextContent('1 ready')
    expect(screen.getByTestId('tailoring-summary')).toHaveTextContent('1 failed')
  })
})
