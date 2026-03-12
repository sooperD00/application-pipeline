import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import JDCard from '../components/JDCard'

// Minimal JD fixture matching the JDRead response shape
function makeJD(overrides = {}) {
  return {
    id: 'jd-001',
    session_id: 'sess-001',
    number: 3,
    company: 'Murmuration',
    role: 'Senior Data Engineer',
    status: 'pending',
    status_source: 'ai',
    cleaned_text: 'Some JD text',
    analysis_text: null,
    compensation: null,
    employee_count: null,
    link: null,
    cover_letter_requested: false,
    flagged_for_review: false,
    created_at: '2026-03-09T00:00:00Z',
    ...overrides,
  }
}

describe('JDCard', () => {
  it('renders the JD number, company, and role', () => {
    render(<JDCard jd={makeJD()} />)

    expect(screen.getByText('3')).toBeInTheDocument()
    expect(screen.getByText('Murmuration')).toBeInTheDocument()
    expect(screen.getByText('Senior Data Engineer')).toBeInTheDocument()
  })

  it('shows "Untitled" when company is empty', () => {
    render(<JDCard jd={makeJD({ company: '' })} />)
    expect(screen.getByText('Untitled')).toBeInTheDocument()
  })

  it('shows "Role not specified" when role is empty', () => {
    render(<JDCard jd={makeJD({ role: '' })} />)
    expect(screen.getByText('Role not specified')).toBeInTheDocument()
  })

  it.each([
    ['pending', 'Pending'],
    ['apply', 'Apply'],
    ['maybe', 'Maybe'],
    ['no', 'No'],
  ])('shows correct label for status="%s"', (status, expectedLabel) => {
    render(<JDCard jd={makeJD({ status })} />)
    expect(screen.getByText(expectedLabel)).toBeInTheDocument()
  })

  it('sets data-status attribute for CSS/test targeting', () => {
    render(<JDCard jd={makeJD({ status: 'apply' })} />)
    const card = screen.getByTestId('jd-card')
    expect(card).toHaveAttribute('data-status', 'apply')
  })
})
