// BDD (Behavior-Driven Development) test structure:
// describe() groups tests; it() names a single behavior as a readable sentence
// "it renders the nav bar" — the string is what prints in terminal output on pass/fail
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'  // keeps routing state entirely in memory (no real browser History API)
import App from '../App'

function renderAt(path) {
  return render(
    // initialEntries: tells the router "pretend the user navigated to this URL"
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>
  )
}

describe('App shell', () => {
  it('renders the nav bar with all tab links', () => {
    renderAt('/')

    // screen: queries the rendered DOM as a user would perceive it (not by class/id)
    expect(screen.getByText('ApplicationPipeline')).toBeInTheDocument()

    // getByRole queries the accessibility tree — asserts these are real <a> tags, not styled divs
    // regex with /i flag: case-insensitive for resilience against capitalization changes
    // toBeInTheDocument() comes from @testing-library/jest-dom (see setup files)
    expect(screen.getByRole('link', { name: /scrape & analyze/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /calibrate/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /review & enrich/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /tailoring/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /resumes/i })).toBeInTheDocument()
  })

  it('redirects / to /sessions (Scrape & Analyze page)', () => {
    renderAt('/')
    expect(screen.getByRole('heading', { name: /scrape & analyze/i })).toBeInTheDocument()
  })

  it('renders each route at its path', () => {
    const routes = [
      ['/sessions', /scrape & analyze/i],
      ['/calibrate', /calibrate/i],
      ['/review', /review & enrich/i],
      ['/tailoring', /tailoring/i],
      ['/resumes', /resumes/i],
    ]
    for (const [path, heading] of routes) {
      const { unmount } = renderAt(path)  // destructure unmount to clean up DOM between iterations
      expect(screen.getByRole('heading', { name: heading })).toBeInTheDocument()
      unmount()  // without this, previous renders persist and getByRole could match stale elements
    }
  })
})