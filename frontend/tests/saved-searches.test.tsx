import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { CandidateFiltersDto, SavedCandidateSearchDto } from '@/entities/candidate'
import { sessionStore } from '@/entities/session'
import type { UserRole } from '@/entities/user'
import type {
  SavedVacancySearchDto,
  VacancyFeedPresetsDto,
  VacancySearchSaveDto,
} from '@/entities/vacancy'
import { mockFetch, renderApp } from './test-utils'

// The first render loads the lazy page chunk, which can take longer than the default 1 s.
const SLOW = { timeout: 5000 }

function signIn(role: UserRole) {
  sessionStore.set({
    accessToken: 't',
    user: { id: 'u1', email: 'u@fsp.ru', role, isEmailVerified: true, createdAt: '2026-01-01' },
  })
}

type Call = { method: string; path: string; body: unknown }

/** A `fetch` answering by method and path (a string is an event stream) that keeps every call. */
function stubFetch(answer: (call: Call) => unknown): Call[] {
  const calls: Call[] = []
  const rest = mockFetch({})
  vi.stubGlobal('fetch', async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = new URL(String(input), 'http://localhost')
    const call: Call = {
      method: init?.method ?? 'GET',
      path: url.pathname.replace('/api/v1', ''),
      body: init?.body ? JSON.parse(String(init.body)) : undefined,
    }
    calls.push(call)
    const body = answer(call)
    if (body === undefined) return rest(input)
    const stream = typeof body === 'string'
    return new Response(stream ? body : JSON.stringify(body), {
      status: 200,
      headers: { 'Content-Type': stream ? 'text/event-stream' : 'application/json' },
    })
  })
  return calls
}

const emptyPage = { items: [], total: 0, page: 1, perPage: 10, pages: 0 }

const noFilters: CandidateFiltersDto = {
  specializations: [],
  grades: [],
  verifiedOnly: false,
  hasFsp: null,
  fspResult: null,
  fspDiscipline: null,
  experienceMin: null,
  stack: [],
  nice: [],
  salaryMin: null,
  salaryMax: null,
  workFormats: [],
  cities: [],
  cityIds: [],
  relocation: true,
  employmentTypes: [],
  jobStatuses: [],
  activeDays: null,
}

const backendSearch: SavedCandidateSearchDto = {
  id: 's1',
  title: 'Backend-разработка · Middle',
  summary: 'Удалённо',
  filters: {
    ...noFilters,
    specializations: ['backend'],
    grades: ['middle'],
    workFormats: ['remote'],
  },
  text: null,
  vacancyId: null,
  count: 12,
  newCount: 3,
  createdAt: '2026-10-08T10:00:00Z',
}

const profilePresets: VacancyFeedPresetsDto = {
  personalized: true,
  profile: {
    salaryMin: 250_000,
    workFormats: ['remote'],
    cities: [],
    relocation: false,
    employmentTypes: ['full'],
    stack: [],
    nice: ['Python'],
    benefits: [],
    accredited: false,
  },
  profileCount: 11,
  category: null,
  freeCount: 94,
}

describe('saved searches', () => {
  afterEach(() => {
    sessionStore.clear()
    vi.restoreAllMocks()
  })

  it('opens a saved search with new candidates and saves the changed one', async () => {
    signIn('employer')
    const saved: SavedCandidateSearchDto[] = [backendSearch]
    const calls = stubFetch(({ method, path, body }) => {
      if (path === '/candidates') return { ...emptyPage, engine: 'database' }
      if (path === '/candidates/saved-searches' && method === 'GET') return saved
      if (path === '/candidates/saved-searches/s1/seen') return { ...backendSearch, newCount: 0 }
      if (path === '/candidates/saved-searches' && method === 'POST') {
        const created = {
          ...backendSearch,
          id: 's2',
          filters: (body as { filters: CandidateFiltersDto }).filters,
          newCount: 0,
        }
        saved.push(created)
        return created
      }
      return undefined
    })
    const user = userEvent.setup()
    const { router } = renderApp('/feed')
    const params = () => new URLSearchParams(router.state.location.search)

    await user.click(
      await screen.findByRole('button', { name: 'Подбор под вакансию: Свободный поиск' }, SLOW),
    )
    const option = await screen.findByRole('option', { name: /Backend-разработка · Middle/ })
    expect(option).toHaveTextContent('+3 новых')

    await user.click(option)
    expect(params().get('saved')).toBe('s1')
    expect(params().getAll('specialization')).toEqual(['backend'])
    expect(params().getAll('workFormat')).toEqual(['remote'])
    await waitFor(() =>
      expect(calls).toContainEqual({
        method: 'POST',
        path: '/candidates/saved-searches/s1/seen',
        body: undefined,
      }),
    )
    expect(screen.getAllByText('из поиска').length).toBeGreaterThan(0)
    expect(screen.getByRole('button', { name: '★ Поиск сохранён' })).toBeDisabled()

    // Another grade: a new search to save, and the list now shows that one.
    await user.click(screen.getByRole('button', { name: 'Senior' }))
    await user.click(screen.getByRole('button', { name: '☆ Сохранить поиск' }))
    const request = calls.find(
      (call) => call.method === 'POST' && call.path === '/candidates/saved-searches',
    )
    expect(request?.body).toMatchObject({ filters: { grades: ['middle', 'senior'] } })
    expect(await screen.findByRole('button', { name: '★ Поиск сохранён' })).toBeDisabled()
    expect(params().get('saved')).toBe('s2')
  })

  it('saves the candidate feed filters from the mode menu', async () => {
    signIn('candidate')
    const calls = stubFetch(({ method, path, body }) => {
      if (path === '/vacancies/feed') return { ...emptyPage, personalized: true, basis: null }
      if (path === '/vacancies/feed/presets') return profilePresets
      if (path === '/vacancies/feed/saved-searches' && method === 'GET') return []
      if (path === '/vacancies/feed/saved-searches' && method === 'POST') {
        const request = body as VacancySearchSaveDto
        const created: SavedVacancySearchDto = {
          id: 'v1',
          title: 'Удалённо · от 250 000 ₽',
          summary: 'по профилю',
          mode: request.mode,
          filters: request.filters,
          count: 11,
          newCount: 0,
          createdAt: '2026-10-08T10:00:00Z',
        }
        return created
      }
      return undefined
    })
    const user = userEvent.setup()
    const { router } = renderApp('/feed')

    await user.click(
      await screen.findByRole('button', { name: 'Основа ленты: Подбор по профилю' }, SLOW),
    )
    await user.click(screen.getByRole('button', { name: '+ Сохранить текущие фильтры' }))

    expect(await screen.findByText('Поиск «Удалённо · от 250 000 ₽» сохранён')).toBeInTheDocument()
    const request = calls.find(
      (call) => call.method === 'POST' && call.path === '/vacancies/feed/saved-searches',
    )
    expect(request?.body).toEqual({ mode: 'profile', filters: profilePresets.profile })
    expect(new URLSearchParams(router.state.location.search).get('saved')).toBe('v1')
  })

  it('tells about new results of a saved search', async () => {
    signIn('employer')
    const event = {
      type: 'saved_search_new',
      searchId: 's1',
      kind: 'candidates',
      title: 'Backend-разработка · Middle',
      count: 3,
    }
    stubFetch(({ path }) => {
      if (path === '/notifications/stream') return `data: ${JSON.stringify(event)}\n\n`
      if (path === '/candidates') return { ...emptyPage, engine: 'database' }
      return undefined
    })

    renderApp('/feed')

    expect(
      await screen.findByText(
        'Сохранённый поиск «Backend-разработка · Middle»: 3 новых кандидата',
        {},
        SLOW,
      ),
    ).toBeInTheDocument()
  })
})
