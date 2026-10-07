import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { CandidateMatchDto, CandidateSearchDto } from '@/entities/candidate'
import { sessionStore } from '@/entities/session'
import type { UserRole } from '@/entities/user'
import type { VacancyFeedDto, VacancyMatchDto } from '@/entities/vacancy'
import { mockFetch, renderApp, stubApi } from './test-utils'

// The first render loads the lazy page chunk, which can take longer than the default 1 s.
const SLOW = { timeout: 5000 }

function signIn(role: UserRole) {
  sessionStore.set({
    accessToken: 't',
    user: { id: 'u1', email: 'u@fsp.ru', role, isEmailVerified: true, createdAt: '2026-01-01' },
  })
}

const category = {
  code: 'backend:middle',
  label: 'Backend-разработка · Middle',
  specialization: 'backend',
  grade: 'middle' as const,
}

function vacancyMatch(id: string, title: string, matchScore: number): VacancyMatchDto {
  return {
    vacancy: {
      id,
      title,
      company: {
        id: 'c1',
        name: 'ПэйФлоу',
        industry: 'Финтех',
        city: 'Москва',
        size: '501–1000',
        itAccredited: true,
        hasLogo: false,
      },
      category,
      stack: ['Python', 'Kafka'],
      salary: { from: 200_000, to: 300_000 },
      workFormat: 'remote',
      city: null,
      description: 'Команда процессинга.\n\nЗадачи:\n— разработка сервисов.',
      publishedAt: '2026-10-05T10:00:00Z',
      grades: ['middle'],
      stackRequired: ['Python', 'Kafka'],
      stackNice: [],
      relocationHelp: false,
      employmentTypes: ['full'],
      benefits: [],
      verifiedGradeOnly: true,
      fspBestResult: null,
      fspDiscipline: null,
      minExperienceYears: null,
    },
    matchScore,
    reasons: ['Ваша категория: Backend-разработка · Middle'],
    reaction: null,
    matched: false,
  }
}

function page<T>(items: T[]) {
  return { items, total: items.length, page: 1, perPage: 10, pages: 1 }
}

const vacancyFeed: VacancyFeedDto = {
  ...page([
    vacancyMatch('v1', 'Go-разработчик в команду антифрода', 0.91),
    {
      ...vacancyMatch('v2', 'Python-разработчик', 0.7),
      reasons: ['Смежная специализация: Fullstack-разработка'],
    },
  ]),
  personalized: true,
  basis: {
    category,
    gradeVerified: true,
    stack: ['Python', 'Kafka'],
    workFormats: ['remote'],
    city: 'Москва',
    salaryExpectation: 250_000,
  },
}

const candidateMatch: CandidateMatchDto = {
  candidate: {
    id: 'p1',
    displayName: 'Марина Крылова',
    headline: 'Middle Backend-разработчик (Python)',
    about: null,
    category,
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
    fspAchievements: [
      {
        eventName: 'Чемпионат Москвы по спортивному программированию',
        year: 2025,
        place: 1,
        discipline: 'algorithmic',
        level: 'regional',
      },
    ],
    fspLinked: true,
    contacts: null,
    jobStatus: 'open',
    employmentTypes: ['full'],
    experienceEntries: [],
    noExperience: false,
    education: [],
    githubUrl: null,
    isMinor: false,
    lastActiveAt: null,
  },
  matchScore: null,
  profileStrength: 0.85,
  reasons: ['Грейд подтверждён тестом: 91 из 100'],
  reaction: null,
  matched: false,
}

const candidateSearch: CandidateSearchDto = { ...page([candidateMatch]), engine: 'elasticsearch' }

describe('feeds', () => {
  afterEach(() => {
    sessionStore.clear()
    vi.restoreAllMocks()
  })

  it('lists the relevant vacancies with notes and opens one on the side sheet', async () => {
    signIn('candidate')
    vi.stubGlobal('fetch', mockFetch({ '/api/v1/vacancies/feed': { body: vacancyFeed } }))
    const user = userEvent.setup()

    renderApp('/feed')

    const row = await screen.findByRole(
      'button',
      { name: /Go-разработчик в команду антифрода/ },
      SLOW,
    )
    // A row carries only what is worth a note; the full card is on the sheet.
    expect(screen.getByText('Смежная специализация: Fullstack-разработка')).toBeInTheDocument()
    expect(screen.getByText('Найдено: 2')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Свайпы' })).toBeInTheDocument()

    await user.click(row)
    const sheet = await screen.findByRole('dialog', { name: 'Go-разработчик в команду антифрода' })
    expect(within(sheet).getByText('Команда процессинга.')).toBeInTheDocument()
  })

  it('shows the recruiter search with profile strength, the engine and FSP on the sheet', async () => {
    signIn('employer')
    vi.stubGlobal(
      'fetch',
      mockFetch({
        '/api/v1/candidates': { body: candidateSearch },
        '/api/v1/vacancies/mine': { body: page([]) },
        '/api/v1/categories/dictionary': { body: { specializations: [], grades: [] } },
      }),
    )
    const user = userEvent.setup()

    renderApp('/feed')

    expect(await screen.findByText('Марина Крылова', {}, SLOW)).toBeInTheDocument()
    expect(screen.getByText('Сила профиля')).toBeInTheDocument()
    expect(screen.getByText('Поиск: Elasticsearch')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /Марина Крылова/ }))
    const sheet = await screen.findByRole('dialog', { name: 'Марина Крылова' })
    expect(within(sheet).getByText(/1-е место · Чемпионат Москвы/)).toBeInTheDocument()
  })

  it('moves to the next card after a swipe decision', async () => {
    signIn('candidate')
    vi.stubGlobal(
      'fetch',
      mockFetch({
        '/api/v1/vacancies/feed': { body: vacancyFeed },
        '/api/v1/vacancies/v1/reaction': { body: { kind: 'like', updatedAt: '2026-10-06' } },
      }),
    )
    const user = userEvent.setup()

    renderApp('/feed/swipe')
    await screen.findAllByText('Go-разработчик в команду антифрода', {}, SLOW)
    await user.click(screen.getByRole('button', { name: 'Интересно' }))

    await waitFor(
      () =>
        expect(screen.queryByText('Go-разработчик в команду антифрода')).not.toBeInTheDocument(),
      { timeout: 2500 },
    )
    expect(screen.getAllByText('Python-разработчик').length).toBeGreaterThan(0)
  })

  it('shows the finished queue inside the film frame without swipe controls', async () => {
    signIn('candidate')
    vi.stubGlobal(
      'fetch',
      mockFetch({
        '/api/v1/vacancies/feed': {
          body: { ...page([]), personalized: false, basis: null },
        },
      }),
    )

    renderApp('/feed/swipe')

    expect(
      await screen.findByText('Вы посмотрели все подходящие вакансии', {}, SLOW),
    ).toBeInTheDocument()
    expect(
      screen.getByText('Отобранные — в ленте, раздел «Отобрано». Новые появятся здесь сами.'),
    ).toBeInTheDocument()
    expect(document.querySelector('.reel__placeholder')).toBeTruthy()
    expect(screen.queryByRole('button', { name: 'Интересно' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Пропустить' })).not.toBeInTheDocument()
  })

  it('skips with the arrow key and applies a decision at once under reduced motion', async () => {
    signIn('candidate')
    vi.stubGlobal('matchMedia', (query: string) => ({
      matches: query.includes('prefers-reduced-motion'),
      media: query,
      addEventListener: () => {},
      removeEventListener: () => {},
    }))
    const calls = stubApi(({ method, path }) => {
      if (path === '/vacancies/feed') return vacancyFeed
      if (path === '/vacancies/reactions/counts') return { liked: 0, matched: 0, skipped: 0 }
      return method === 'GET' ? [] : { kind: 'skip', updatedAt: '2026-10-06' }
    })
    const user = userEvent.setup()

    renderApp('/feed/swipe')
    await screen.findAllByText('Go-разработчик в команду антифрода', {}, SLOW)
    await user.keyboard('{ArrowLeft}')

    // No animation to wait for: the next card is the current one right away.
    expect(screen.queryByText('Go-разработчик в команду антифрода')).not.toBeInTheDocument()
    await waitFor(() => expect(calls.some((call) => call.method === 'PUT')).toBe(true))
    const saved = calls.find((call) => call.method === 'PUT')
    expect([saved?.path, saved?.body]).toEqual(['/vacancies/v1/reaction', { kind: 'skip' }])
    // The deck is not left locked after a decision.
    expect(screen.getByRole('button', { name: 'Пропустить' })).toBeEnabled()
  })

  it('opens the whole vacancy on one sheet from a frame of the reel', async () => {
    signIn('candidate')
    stubApi(({ method, path }) => {
      if (path === '/vacancies/feed') return vacancyFeed
      if (path === '/companies/c1')
        return { id: 'c1', name: 'ПэйФлоу', description: 'Платёжный сервис для магазинов.' }
      if (path === '/vacancies/reactions/counts') return { liked: 0, matched: 0, skipped: 0 }
      return method === 'GET' ? [] : undefined
    })
    // The details button appears only when the text does not fit the frame; jsdom has no layout.
    vi.spyOn(HTMLElement.prototype, 'scrollHeight', 'get').mockReturnValue(900)
    vi.spyOn(HTMLElement.prototype, 'clientHeight', 'get').mockReturnValue(400)
    const user = userEvent.setup()

    renderApp('/feed/swipe')
    await screen.findAllByText('Go-разработчик в команду антифрода', {}, SLOW)
    await user.click(await screen.findByRole('button', { name: 'Изучить подробнее' }))

    const sheet = await screen.findByRole('dialog', { name: 'Go-разработчик в команду антифрода' })
    // Both blocks of the description, not only the lead shown on the frame.
    expect(within(sheet).getByText('Команда процессинга.')).toBeInTheDocument()
    expect(within(sheet).getByText(/— разработка сервисов/)).toBeInTheDocument()
    expect(await within(sheet).findByText('Платёжный сервис для магазинов.')).toBeInTheDocument()

    // Arrow keys belong to the sheet while it is open: the card behind stays.
    await user.keyboard('{ArrowRight}')
    await user.click(within(sheet).getByRole('button', { name: 'Закрыть' }))
    expect(screen.getAllByText('Go-разработчик в команду антифрода').length).toBeGreaterThan(0)
  })

  it('counts the decisions above the reel and links each number to its list', async () => {
    signIn('employer')
    stubApi(({ method, path }) => {
      if (path === '/candidates') return candidateSearch
      if (path === '/candidates/reactions/counts') return { liked: 12, matched: 3, skipped: 40 }
      return method === 'GET' ? [] : undefined
    })

    renderApp('/feed/swipe')
    const counters = await screen.findByRole('navigation', { name: 'Мои решения' }, SLOW)

    await waitFor(() => expect(within(counters).getByText('12')).toBeInTheDocument())
    const links = within(counters).getAllByRole('link')
    expect(links.map((link) => [link.textContent, link.getAttribute('href')])).toEqual([
      ['Отобрано12', '/feed?view=liked'],
      ['Взаимно3', '/feed?view=matched'],
      ['Вырезано40', '/feed?view=skipped'],
    ])
  })

  it('opens the lists of own decisions from the feed and marks mutual interest', async () => {
    signIn('candidate')
    const views: (string | null)[] = []
    vi.stubGlobal('fetch', async (input: RequestInfo | URL) => {
      const url = new URL(String(input), 'http://localhost')
      const view = url.searchParams.get('view')
      // The app also restores the session and checks the resume on start: only the feed counts.
      if (url.pathname.endsWith('/vacancies/feed')) views.push(view)
      const items =
        view === 'matched'
          ? [{ ...vacancyMatch('v1', 'Go-разработчик в команду антифрода', 0.91), matched: true }]
          : view === 'skipped'
            ? []
            : vacancyFeed.items
      return new Response(JSON.stringify({ ...vacancyFeed, ...page(items) }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    })
    const user = userEvent.setup()

    renderApp('/feed')
    await screen.findByText('Python-разработчик', {}, SLOW)
    expect(screen.queryByText(/Взаимно: компания/)).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Взаимно' }))
    expect(await screen.findByText('Взаимно: компания отобрала вас')).toBeInTheDocument()
    expect(screen.queryByText('Python-разработчик')).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Вырезано' }))
    expect(await screen.findByText('Ничего не вырезано')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Отобрано' }))
    await screen.findByText('Python-разработчик')
    expect(views).toEqual(['all', 'matched', 'skipped', 'liked'])
  })
})
