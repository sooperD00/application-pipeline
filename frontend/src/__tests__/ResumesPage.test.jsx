import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import ResumesPage from '../pages/ResumesPage'
import * as client from '../api/client'

// Mock the entire client module — we control every API response
vi.mock('../api/client')

// ── Fixtures ────────────────────────────────────────────────────────────────

const RESUME_A = {
  id: 'resume-aaa',
  user_id: 'user-001',
  label: 'Technical',
  content: 'Nicole Chen\nStaff Data Platform Engineer\n13 years at Intel\nPython, SQL, Kafka',
  created_at: '2026-03-01T00:00:00Z',
}

const RESUME_B = {
  id: 'resume-bbb',
  user_id: 'user-001',
  label: 'Leadership',
  content: 'Nicole Chen\nMentor of the Year 2022\nLed Edge-to-Cloud architecture across 5 sites',
  created_at: '2026-03-02T00:00:00Z',
}

const RESUME_C = {
  id: 'resume-ccc',
  user_id: 'user-001',
  label: 'Platform',
  content: 'Nicole Chen\nDistributed systems specialist\nKafka, FastAPI, dbt',
  created_at: '2026-03-03T00:00:00Z',
}

function renderResumesPage() {
  return render(
    <MemoryRouter initialEntries={['/resumes']}>
      <ResumesPage />
    </MemoryRouter>
  )
}

// ── Tests ────────────────────────────────────────────────────────────────────

describe('ResumesPage', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('renders resume cards after loading', async () => {
    client.listResumes.mockResolvedValue([RESUME_A, RESUME_B])

    renderResumesPage()

    await waitFor(() => {
      expect(screen.getByText('Technical')).toBeInTheDocument()
    })
    expect(screen.getByText('Leadership')).toBeInTheDocument()

    // Counter shows 2/3
    expect(screen.getByText('2/3')).toBeInTheDocument()

    // Two cards rendered
    const cards = screen.getAllByTestId('resume-card')
    expect(cards).toHaveLength(2)
  })

  it('shows empty state when no resumes exist', async () => {
    client.listResumes.mockResolvedValue([])

    renderResumesPage()

    await waitFor(() => {
      expect(screen.getByText(/no resumes yet/i)).toBeInTheDocument()
    })
    expect(screen.getByText('0/3')).toBeInTheDocument()
  })

  it('add resume → card appears', async () => {
    const user = userEvent.setup()

    const newResume = {
      id: 'resume-new',
      user_id: 'user-001',
      label: 'Platform',
      content: 'New resume content here',
      created_at: '2026-03-10T00:00:00Z',
    }

    // First fetch: 1 resume. After create + refresh: 2 resumes.
    client.listResumes
      .mockResolvedValueOnce([RESUME_A])
      .mockResolvedValueOnce([RESUME_A, newResume])

    client.createResume.mockResolvedValue(newResume)

    renderResumesPage()

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('Technical')).toBeInTheDocument()
    })

    // Click "+ Add Resume" button to open form
    const addButton = screen.getByRole('button', { name: /add resume/i })
    await user.click(addButton)

    // Fill out the form
    const labelInput = screen.getByPlaceholderText(/technical/i)
    await user.type(labelInput, 'Platform')

    const contentInput = screen.getByPlaceholderText(/paste your full resume/i)
    await user.type(contentInput, 'New resume content here')

    // Submit
    const saveButton = screen.getByRole('button', { name: /save resume/i })
    await user.click(saveButton)

    // createResume called with correct args
    expect(client.createResume).toHaveBeenCalledWith({
      label: 'Platform',
      content: 'New resume content here',
    })

    // After refresh, new card appears
    await waitFor(() => {
      expect(screen.getByText('Platform')).toBeInTheDocument()
    })
    expect(screen.getByText('2/3')).toBeInTheDocument()
  })

  it('delete resume → card removed', async () => {
    const user = userEvent.setup()

    // First fetch: 2 resumes. After delete + refresh: 1 resume.
    client.listResumes
      .mockResolvedValueOnce([RESUME_A, RESUME_B])
      .mockResolvedValueOnce([RESUME_B])

    client.deleteResume.mockResolvedValue(null)

    renderResumesPage()

    await waitFor(() => {
      expect(screen.getByText('Technical')).toBeInTheDocument()
    })

    // Find the Technical card and click Delete
    const cards = screen.getAllByTestId('resume-card')
    const technicalCard = cards.find(card =>
      within(card).queryByText('Technical')
    )
    const deleteButton = within(technicalCard).getByRole('button', { name: /delete/i })
    await user.click(deleteButton)

    // Confirmation appears — click "Yes, delete"
    const confirmButton = within(technicalCard).getByRole('button', { name: /yes, delete/i })
    await user.click(confirmButton)

    expect(client.deleteResume).toHaveBeenCalledWith('resume-aaa')

    // After refresh, Technical card is gone
    await waitFor(() => {
      expect(screen.queryByText('Technical')).not.toBeInTheDocument()
    })
    expect(screen.getByText('1/3')).toBeInTheDocument()
  })

  it('disables add button at cap (3 resumes)', async () => {
    client.listResumes.mockResolvedValue([RESUME_A, RESUME_B, RESUME_C])

    renderResumesPage()

    await waitFor(() => {
      expect(screen.getByText('3/3')).toBeInTheDocument()
    })

    // The "+ Add Resume" button should be disabled
    const addButton = screen.getByRole('button', { name: /add resume/i })
    expect(addButton).toBeDisabled()
  })
})
