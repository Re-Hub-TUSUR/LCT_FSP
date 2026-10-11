import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type {
  CandidateFacetsDto,
  CandidatePresetsDto,
  CandidateSearchDto,
} from '@/entities/candidate'
import { sessionStore } from '@/entities/session'
import type { UserRole } from '@/entities/user'
import type { VacancyFacetsDto, VacancyFeedDto, VacancyFeedPresetsDto } from '@/entities/vacancy'
import { mockFetch, renderApp } from './test-utils'

// The first render loads the lazy page chunk, which can take longer than the default 1 s.
const SLOW = { timeout: 5000 }

function signIn(role: UserRole) {
  sessionStore.set({
    accessToken: 't',
    user: { id: 'u1', email: 'u@fsp.ru', role, isEmailVerified: true, createdAt: '2026-01-01' },
  })
}

/** A `fetch` answering JSON by path that keeps every URL asked for. */
function recordFetch(handlers: Record<string, (url: URL) => unknown>): URL[] {
  const urls: URL[] = []
  const rest = mockFetch({})
  vi.stubGlobal('fetch', async (input: RequestInfo | URL) => {
    const url = new URL(String(input), 'http://localhost')
    urls.push(url)
    const answer = handlers[url.pathname]
    if (!answer) return rest(input)
    return new Response(JSON.stringify(answer(url)), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    })
  })
  return urls
}

const requestsTo = (urls: URL[], path: string) =>
  urls.filter((url) => url.pathname === `/api/v1${path}`)

const option = (value: string, count: number) => ({ value, count })
const emptyPage = { items: [], total: 0, page: 1, perPage: 10, pages: 0 }

const dictionary = {
  specializations: [{ code: 'backend', label: 'Backend-разработка' }],
  grades: [],
  synonyms: [['python', 'питон', 'пайтон']],
}

const search: CandidateSearchDto = { ...emptyPage, engine: 'database' }

const candidateFacets: CandidateFacetsDto = {
  total: 120,
  count: 37,
  specializations: [option('backend', 28)],
  grades: [
    option('intern', 0),
    option('junior', 9),
    option('middle', 14),
    option('senior', 10),
    option('lead', 4),
  ],
  verified: 30,
  fsp: 12,
  fspResults: [option('participant', 12), option('finalist', 8), option('prizewinner', 5)],
  fspDisciplines: [option('algorithmic', 6), option('product', 7)],
  experience: [option('1', 30), option('3', 20), option('5', 8)],
  workFormats: [option('office', 5), option('hybrid', 20), option('remote', 25)],
  cities: [option('Москва', 15), option('Тюмень', 3)],
  relocation: 40,
  employmentTypes: [option('full', 35), option('part', 6)],
  jobStatuses: [option('active', 15), option('open', 22)],
  active: 18,
  stack: [option('Python', 30), option('Docker', 20), option('Kafka', 12), option('Go', 2)],
  relaxations: [],
}

const candidatePresets: CandidatePresetsDto = {
  total: 120,
  vacancies: [
    {
      vacancyId: 'v1',
      title: 'Python-разработчик',
      workFormat: 'hybrid',
      city: 'Тюмень',
      salaryTo: 350_000,
      published: true,
      count: 12,
      filters: {
        specializations: ['backend'],
        grades: ['middle', 'senior'],
        verifiedOnly: true,
        hasFsp: null,
        fspResult: null,
        fspDiscipline: null,
        experienceMin: 1,
        stack: ['Python'],
        nice: ['Kafka'],
        salaryMin: null,
        salaryMax: 350_000,
        workFormats: ['hybrid'],
        cities: ['Тюмень'],
        cityIds: [],
        relocation: true,
        employmentTypes: ['full'],
        jobStatuses: [],
        activeDays: null,
      },
    },
  ],
}

const vacancyFeed: VacancyFeedDto = { ...emptyPage, personalized: true, basis: null }

const vacancyPresets: VacancyFeedPresetsDto = {
  personalized: true,
  profile: {
    salaryMin: 250_000,
    workFormats: ['remote'],
    cities: [],
    relocation: false,
    employmentTypes: ['full'],
    stack: [],
    nice: ['Python', 'Kafka'],
    benefits: [],
    accredited: false,
  },
  profileCount: 11,
  category: {
    code: 'backend:middle',
    label: 'Backend-разработка · Middle',
    specialization: 'backend',
    grade: 'middle',
  },
  freeCount: 94,
}

const vacancyFacets: VacancyFacetsDto = {
  total: 32,
  count: 11,
  workFormats: [option('office', 13), option('hybrid', 17), option('remote', 11)],
  employmentTypes: [option('full', 11), option('part', 14), option('project', 11)],
  benefits: [option('dms', 6), option('flexible_start', 4), option('labor_code', 11)],
  accredited: 2,
  cities: [option('Москва', 8)],
  stack: [option('PostgreSQL', 21), option('Python', 14)],
  relaxations: [],
}

describe('feed filters', () => {
  afterEach(() => {
    sessionStore.clear()
    vi.restoreAllMocks()
  })

  it('fills the recruiter filters from a vacancy, marks them and undoes the choice', async () => {
    signIn('employer')
    const urls = recordFetch({
      '/api/v1/candidates': () => search,
      '/api/v1/candidates/facets': () => candidateFacets,
      '/api/v1/candidates/presets': () => candidatePresets,
      '/api/v1/categories/dictionary': () => dictionary,
    })
    const user = userEvent.setup()
    const { router } = renderApp('/feed')
    const params = () => new URLSearchParams(router.state.location.search)

    const mode = await screen.findByRole(
      'button',
      { name: 'Подбор под вакансию: Свободный поиск' },
      SLOW,
    )
    // Every option says how many candidates choosing it alone would leave.
    expect(await screen.findByText('кандидатов из 120')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Middle 14' }))
    expect(params().getAll('grade')).toEqual(['middle'])

    await user.click(mode)
    await user.click(screen.getByRole('option', { name: /Python-разработчик/ }))
    expect(screen.getByText('Фильтры заполнены из вакансии')).toBeInTheDocument()
    expect(params().get('vacancyId')).toBe('v1')
    expect(params().getAll('grade')).toEqual(['middle', 'senior'])
    expect(params().getAll('stack')).toEqual(['Python'])
    expect(params().getAll('nice')).toEqual(['Kafka'])
    expect(params().get('salaryMax')).toBe('350000')
    await waitFor(() =>
      expect(requestsTo(urls, '/candidates').at(-1)?.searchParams.get('vacancyId')).toBe('v1'),
    )
    expect(screen.getAllByText('из вакансии').length).toBeGreaterThan(1)

    // A required skill taken out: the stack is marked as changed and comes back on request.
    const stack = screen.getByRole('group', { name: 'Стек' })
    await user.click(within(stack).getByRole('button', { name: 'Убрать Python' }))
    await user.click(within(stack).getByRole('button', { name: 'вернуть' }))
    expect(params().getAll('stack')).toEqual(['Python'])

    // The toast takes back the vacancy and its filters: the chosen grade is there again.
    await user.click(screen.getByRole('button', { name: 'Вернуть' }))
    expect(params().get('vacancyId')).toBeNull()
    expect(params().getAll('grade')).toEqual(['middle'])
  })

  it('hides the vacancy note for this tab, or for good', async () => {
    signIn('employer')
    recordFetch({
      '/api/v1/candidates': () => search,
      '/api/v1/candidates/facets': () => candidateFacets,
      '/api/v1/candidates/presets': () => candidatePresets,
      '/api/v1/categories/dictionary': () => dictionary,
    })
    const user = userEvent.setup()

    const { unmount } = renderApp('/feed')

    expect(
      await screen.findByRole('dialog', { name: 'Выберите вакансию' }, SLOW),
    ).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Понял' }))
    expect(screen.queryByRole('dialog', { name: 'Выберите вакансию' })).not.toBeInTheDocument()
    expect(window.sessionStorage.getItem('kadry.feed.vacancy-hint')).toBe('1')
    expect(window.localStorage.getItem('kadry.onboarding.feed-vacancy')).toBeNull()

    unmount()
    window.sessionStorage.clear()
    renderApp('/feed')
    await user.click(await screen.findByRole('button', { name: 'Больше не показывать' }, SLOW))
    expect(screen.queryByRole('dialog', { name: 'Выберите вакансию' })).not.toBeInTheDocument()
    expect(window.localStorage.getItem('kadry.onboarding.feed-vacancy')).toBe('done')
  })

  it('finds a technology by slang and suggests what to loosen when nobody matches', async () => {
    signIn('employer')
    recordFetch({
      '/api/v1/candidates': () => search,
      '/api/v1/candidates/facets': (url) =>
        url.searchParams.getAll('stack').includes('Go')
          ? {
              ...candidateFacets,
              count: 0,
              relaxations: [
                { kind: 'stack', value: 'Go', count: 4 },
                { kind: 'salary_max', value: null, count: 2 },
              ],
            }
          : candidateFacets,
      '/api/v1/candidates/presets': () => candidatePresets,
      '/api/v1/categories/dictionary': () => dictionary,
    })
    const user = userEvent.setup()
    const { router } = renderApp('/feed?stack=Go&salaryMax=150000')
    const params = () => new URLSearchParams(router.state.location.search)

    expect(await screen.findByText('Никто не подходит', {}, SLOW)).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /Go — перенести в «Будет плюсом»/ }))
    expect(params().getAll('stack')).toEqual([])
    expect(params().getAll('nice')).toEqual(['Go'])
    expect(params().get('salaryMax')).toBe('150000')

    const required = screen.getByRole('combobox', { name: 'Обязательный стек' })
    await user.type(required, 'пит')
    expect(screen.getByRole('option', { name: /Python/ })).toHaveTextContent('по запросу «питон»')
    await user.keyboard('{Enter}')
    expect(params().getAll('stack')).toEqual(['Python'])
  })

  it('starts the candidate feed from the profile and shows what each format adds', async () => {
    signIn('candidate')
    const urls = recordFetch({
      '/api/v1/vacancies/feed': () => vacancyFeed,
      '/api/v1/vacancies/feed/presets': () => vacancyPresets,
      '/api/v1/vacancies/feed/facets': () => vacancyFacets,
      '/api/v1/categories/dictionary': () => dictionary,
    })
    const user = userEvent.setup()
    const { router } = renderApp('/feed')

    const mode = await screen.findByRole(
      'button',
      { name: 'Основа ленты: Подбор по профилю' },
      SLOW,
    )
    // The feed waits for the profile: its very first request already carries the profile.
    await waitFor(() => expect(requestsTo(urls, '/vacancies/feed').length).toBeGreaterThan(0))
    const first = requestsTo(urls, '/vacancies/feed')[0]!.searchParams
    expect(first.get('mode')).toBe('profile')
    expect(first.get('salaryMin')).toBe('250000')
    expect(first.getAll('workFormat')).toEqual(['remote'])
    expect(first.getAll('nice')).toEqual(['Python', 'Kafka'])
    expect(screen.getAllByText('из профиля').length).toBeGreaterThan(0)
    // Remote is chosen: the other formats say how many vacancies they would add.
    expect(await screen.findByRole('button', { name: 'Гибрид +6' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Офис +2' })).toBeInTheDocument()

    await user.click(mode)
    await user.click(screen.getByRole('option', { name: /Свободный поиск/ }))
    const params = new URLSearchParams(router.state.location.search)
    expect(params.get('mode')).toBe('free')
    expect(params.get('salaryMin')).toBeNull()
    expect(params.getAll('nice')).toEqual([])
  })
})
