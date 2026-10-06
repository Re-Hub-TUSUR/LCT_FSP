import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { CandidateMatchDto, CandidateSearchDto } from '@/entities/candidate'
import { sessionStore } from '@/entities/session'
import type { UserRole } from '@/entities/user'
import type { VacancyFeedDto, VacancyMatchDto } from '@/entities/vacancy'
import { mockFetch, renderApp } from './test-utils'

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
      company: { id: 'c1', name: 'ПэйФлоу', industry: 'Финтех', city: 'Москва', size: '501–1000' },
      category,
      stack: ['Python', 'Kafka'],
      salary: { from: 200_000, to: 300_000 },
      workFormat: 'remote',
      city: null,
      description: 'Команда процессинга.\n\nЗадачи:\n— разработка сервисов.',
      publishedAt: '2026-10-05T10:00:00Z',
    },
    matchScore,
    reasons: ['Ваша категория: Backend-разработка · Middle'],
    reaction: null,
  }
}

function page<T>(items: T[]) {
  return { items, total: items.length, page: 1, perPage: 10, pages: 1 }
}

const vacancyFeed: VacancyFeedDto = {
  ...page([
    vacancyMatch('v1', 'Go-разработчик в команду антифрода', 0.91),
    vacancyMatch('v2', 'Python-разработчик', 0.7),
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
  },
  matchScore: null,
  profileStrength: 0.85,
  reasons: ['Грейд подтверждён тестом: 91 из 100'],
  reaction: null,
}

const candidateSearch: CandidateSearchDto = { ...page([candidateMatch]), engine: 'elasticsearch' }

describe('feeds', () => {
  afterEach(() => sessionStore.clear())

  it('shows the candidate relevant vacancies with the match and reasons', async () => {
    signIn('candidate')
    vi.stubGlobal('fetch', mockFetch({ '/api/v1/vacancies/feed': { body: vacancyFeed } }))

    renderApp('/feed')

    expect(
      await screen.findByText('Go-разработчик в команду антифрода', {}, SLOW),
    ).toBeInTheDocument()
    expect(screen.getByText('91%')).toBeInTheDocument()
    expect(screen.getAllByText('Ваша категория: Backend-разработка · Middle')).toHaveLength(2)
    expect(screen.getByText('Найдено: 2')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Свайпы' })).toBeInTheDocument()
  })

  it('shows the recruiter search with profile strength and the engine', async () => {
    signIn('employer')
    vi.stubGlobal(
      'fetch',
      mockFetch({
        '/api/v1/candidates': { body: candidateSearch },
        '/api/v1/vacancies/mine': { body: page([]) },
        '/api/v1/categories/dictionary': { body: { specializations: [], grades: [] } },
      }),
    )

    renderApp('/feed')

    expect(await screen.findByText('Марина Крылова', {}, SLOW)).toBeInTheDocument()
    expect(screen.getByText('Сила профиля')).toBeInTheDocument()
    expect(screen.getByText('Поиск: Elasticsearch')).toBeInTheDocument()
    expect(screen.getByText(/ФСП: 1-е место/)).toBeInTheDocument()
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
      screen.getByText('Понравившиеся — в избранном ленты. Новые появятся здесь сами.'),
    ).toBeInTheDocument()
    expect(document.querySelector('.reel__placeholder')).toBeTruthy()
    expect(screen.queryByRole('button', { name: 'Интересно' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Пропустить' })).not.toBeInTheDocument()
  })
})
