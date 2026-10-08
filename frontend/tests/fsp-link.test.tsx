import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { OwnCandidateDto } from '@/entities/candidate'
import { sessionStore } from '@/entities/session'
import { FspLinkPanel } from '@/features/link-fsp-id'
import type * as CallbackUri from '@/features/link-fsp-id/lib/callback-uri'
import { FspCallbackPage } from '@/pages/fsp-callback'
import { renderApp, renderWithProviders, stubApi } from './test-utils'

type CallbackModule = typeof CallbackUri

const leave = vi.hoisted(() => vi.fn<(url: string) => void>())
vi.mock('@/features/link-fsp-id/lib/callback-uri', async (original) => ({
  ...(await original<CallbackModule>()),
  goToFspId: leave,
}))

const SLOW = { timeout: 5000 }

const PROFILE: OwnCandidateDto = {
  id: 'me',
  displayName: 'Анна Смирнова',
  headline: 'Backend-разработчик',
  about: null,
  category: null,
  gradeVerified: false,
  assessmentScore: null,
  assessmentStatus: 'not_taken',
  stack: ['Python', 'SQL', 'Docker'],
  softSkills: [],
  experienceYears: 3,
  englishLevel: null,
  city: 'Казань',
  relocationReady: false,
  workFormats: ['remote'],
  salaryExpectation: null,
  fspAchievements: [],
  fspTitles: [],
  fspLinked: false,
  contacts: { email: 'anna@example.com', phone: null, telegram: null },
  jobStatus: 'open',
  employmentTypes: ['full'],
  experienceEntries: [],
  noExperience: false,
  education: [],
  githubUrl: null,
  isMinor: false,
  lastActiveAt: null,
  searching: true,
  fspMemberId: null,
  specialization: 'backend',
  birthDate: null,
  profileDisplayConsent: true,
  fspSync: 'yes',
}

const LINKED: OwnCandidateDto = {
  ...PROFILE,
  fspLinked: true,
  fspMemberId: 'FSP-100101',
  fspLinkedAt: '2026-10-08T10:00:00Z',
  fspSyncedAt: '2026-10-08T10:00:00Z',
  fspSyncError: null,
  fspAchievements: [
    {
      eventName: 'Кубок России по спортивному программированию',
      eventKind: 'cup',
      year: 2025,
      place: 2,
      result: 'prizewinner',
      participation: 'team',
      teamName: 'NullPointer',
      discipline: 'algorithmic',
      level: 'national',
    },
  ],
  fspTitles: [{ kind: 'kms', discipline: 'algorithmic', awardedYear: 2025 }],
}

function signIn() {
  sessionStore.set({
    accessToken: 't',
    user: {
      id: 'u1',
      email: 'anna@example.com',
      role: 'candidate',
      isEmailVerified: true,
      createdAt: '2026-01-01T00:00:00Z',
    },
  })
}

describe('FSP ID link', () => {
  afterEach(() => {
    sessionStore.clear()
    vi.unstubAllGlobals()
    leave.mockReset()
  })

  it('starts the FSP ID sign-in instead of asking for an id', async () => {
    signIn()
    const calls = stubApi((call) =>
      call.path === '/fsp-id/authorize'
        ? { authorizeUrl: 'https://id.fsp.example/auth?state=s' }
        : PROFILE,
    )
    renderWithProviders(<FspLinkPanel profile={PROFILE} />)
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()

    await userEvent.setup().click(screen.getByRole('button', { name: 'Привязать ФСП ID' }))

    await waitFor(() => expect(leave).toHaveBeenCalledWith('https://id.fsp.example/auth?state=s'))
    const start = calls.find((call) => call.path === '/fsp-id/authorize')
    expect(start?.body).toEqual({ redirectUri: `${window.location.origin}/profile/fsp/callback` })
  })

  it('shows the imported results and re-reads the registry after a failure', async () => {
    signIn()
    const failed: OwnCandidateDto = {
      ...LINKED,
      fspSyncError: 'Реестр ФСП временно недоступен',
    }
    const calls = stubApi((call) => (call.path === '/candidates/me/fsp-sync' ? LINKED : failed))
    renderWithProviders(<FspLinkPanel profile={failed} justLinked />)

    expect(screen.getByText('ФСП ID привязан.')).toBeInTheDocument()
    expect(screen.getByText('FSP-100101')).toBeInTheDocument()
    expect(screen.getByText('Выгружено из реестра: 1 результат и 1 звание.')).toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent('Реестр ФСП временно недоступен')

    await userEvent.setup().click(screen.getByRole('button', { name: 'Обновить из реестра' }))
    await waitFor(
      () => expect(calls.some((call) => call.path === '/candidates/me/fsp-sync')).toBe(true),
      SLOW,
    )
  })

  it('treats a participant without FSP history as a normal profile', () => {
    signIn()
    stubApi(() => PROFILE)
    renderWithProviders(
      <FspLinkPanel profile={{ ...LINKED, fspAchievements: [], fspTitles: [] }} />,
    )
    expect(screen.getByText(/пока нет ваших результатов/)).toBeInTheDocument()
  })

  it('finishes the link on the callback page and returns to the settings', async () => {
    signIn()
    const calls = stubApi(() => LINKED)
    const { router } = renderApp('/profile/fsp/callback?code=abc&state=xyz', [
      { path: '/profile/fsp/callback', element: <FspCallbackPage /> },
      { path: '/profile/settings', element: <p>Настройки</p> },
    ])

    expect(await screen.findByText('Настройки', {}, SLOW)).toBeInTheDocument()
    expect(router.state.location.search).toBe('?fsp=linked')
    const links = calls.filter((call) => call.path === '/candidates/me/fsp-link')
    expect(links).toEqual([
      { method: 'POST', path: '/candidates/me/fsp-link', body: { code: 'abc', state: 'xyz' } },
    ])
  })

  it('explains a cancelled sign-in without calling the API', () => {
    signIn()
    const calls = stubApi(() => LINKED)
    renderApp('/profile/fsp/callback?error=access_denied&state=xyz', [
      { path: '/profile/fsp/callback', element: <FspCallbackPage /> },
    ])
    expect(screen.getByText('Вход через ФСП ID отменён')).toBeInTheDocument()
    expect(calls).toEqual([])
  })
})
