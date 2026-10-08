import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { CandidateDto } from '@/entities/candidate'
import { sessionStore } from '@/entities/session'
import { mockFetch, renderApp } from './test-utils'

// The first render loads the lazy page chunk, which can take longer than the default 1 s.
const SLOW = { timeout: 5000 }

const candidate: CandidateDto = {
  id: 'p1',
  displayName: 'Марина Крылова',
  headline: 'Middle Backend-разработчик (Python)',
  about: null,
  category: {
    code: 'backend:middle',
    label: 'Backend-разработка · Middle',
    specialization: 'backend',
    grade: 'middle',
  },
  gradeVerified: true,
  assessmentScore: 91.4,
  assessmentStatus: 'passed',
  stack: ['Python', 'FastAPI'],
  softSkills: [],
  experienceYears: 5,
  englishLevel: 'C1',
  city: 'Москва',
  relocationReady: false,
  workFormats: ['remote'],
  salaryExpectation: 270_000,
  fspAchievements: [],
  fspTitles: [],
  fspLinked: false,
  contacts: null,
  jobStatus: 'open',
  employmentTypes: ['full'],
  experienceEntries: [],
  noExperience: false,
  education: [],
  githubUrl: null,
  isMinor: false,
  lastActiveAt: null,
}

describe('resume as a PDF', () => {
  afterEach(() => {
    sessionStore.clear()
    vi.restoreAllMocks()
  })

  it('downloads the resume of a candidate from the profile page', async () => {
    sessionStore.set({
      accessToken: 't',
      user: {
        id: 'u1',
        email: 'hr@fsp.ru',
        role: 'employer',
        isEmailVerified: true,
        createdAt: '2026-01-01',
      },
    })
    const rest = mockFetch({ '/api/v1/candidates/p1': { body: candidate } })
    const requested: string[] = []
    vi.stubGlobal('fetch', async (input: RequestInfo | URL) => {
      const url = new URL(String(input), 'http://localhost')
      requested.push(url.pathname)
      if (url.pathname === '/api/v1/candidates/p1/resume.pdf') {
        return new Response('%PDF-1.7', { headers: { 'Content-Type': 'application/pdf' } })
      }
      return rest(input)
    })
    // jsdom has no object URLs and does not navigate on a click: record what would be saved.
    URL.createObjectURL = vi.fn<(blob: Blob) => string>(() => 'blob:resume')
    URL.revokeObjectURL = vi.fn<(url: string) => void>()
    const saved: string[] = []
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (
      this: HTMLAnchorElement,
    ) {
      saved.push(this.download)
    })
    const user = userEvent.setup()

    renderApp('/candidates/p1')
    await user.click(await screen.findByRole('button', { name: 'Скачать резюме PDF' }, SLOW))

    await waitFor(() => expect(saved).toEqual(['Резюме — Марина Крылова.pdf']))
    expect(requested).toContain('/api/v1/candidates/p1/resume.pdf')
  })
})
