import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { OwnCandidateDto } from '@/entities/candidate'
import { sessionStore } from '@/entities/session'
import { mockFetch, renderApp } from './test-utils'

// The cabinet pulls in the biggest lazy chunk: cold, the first render alone takes ~3.5 s, and the
// suite runs every file in parallel. A wait ceiling, not a delay: a fast render returns at once.
const SLOW = { timeout: 10_000 }

function signIn(role: 'candidate' | 'employer', name?: { firstName: string; lastName: string }) {
  sessionStore.set({
    accessToken: 't',
    user: {
      id: 'u1',
      email: 'dev@fsp.ru',
      role,
      isEmailVerified: true,
      createdAt: '2026-01-01T00:00:00Z',
      ...name,
    },
  })
}

const NO_COMPANY = {
  '/api/v1/companies/me': { body: null },
}

const SAVED_RESUME: OwnCandidateDto = {
  id: 'me',
  displayName: 'Анна Петрова',
  headline: 'Backend-разработчик',
  about: null,
  category: null,
  gradeVerified: false,
  assessmentScore: null,
  assessmentStatus: 'not_taken',
  stack: ['Python', 'PostgreSQL', 'Docker'],
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
  resumes: [],
  hasPhoto: false,
  contacts: { email: 'dev@fsp.ru', phone: null, telegram: '@anna' },
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
  fspSync: 'later',
}

describe('personal cabinet', () => {
  afterEach(() => {
    sessionStore.clear()
    vi.unstubAllGlobals()
  })

  it('starts a candidate without a resume on the first step', async () => {
    signIn('candidate')
    vi.stubGlobal(
      'fetch',
      mockFetch({
        '/api/v1/candidates/me': { body: null },
      }),
    )
    const { router } = renderApp('/feed/swipe')
    const user = userEvent.setup()

    await waitFor(() => expect(router.state.location.pathname).toBe('/profile/resume'), SLOW)
    expect(
      await screen.findByText(/Есть готовое резюме\? Приложите его/, {}, SLOW),
    ).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Свайпы' })).not.toBeInTheDocument()
    expect(screen.getByText(/остальные разделы закрыты/)).toBeInTheDocument()

    const manual = screen.getByRole('button', { name: 'Заполнить вручную' })
    expect(manual).toBeDisabled()
    // The consents were given at registration: only the FSP question is left here.
    expect(screen.queryByRole('checkbox')).not.toBeInTheDocument()
    await user.click(screen.getByLabelText('Да'))
    expect(screen.getByText(/привяжите ФСП ID в настройках/)).toBeInTheDocument()
    expect(screen.queryByLabelText(/ID участника/)).not.toBeInTheDocument()
    await user.click(screen.getByLabelText('Позже'))
    expect(manual).toBeEnabled()

    await user.click(manual)
    expect(screen.getByLabelText('Имя и фамилия')).toBeInTheDocument()
    expect(screen.getByLabelText('Нет опыта')).toBeInTheDocument()
    expect(screen.getByText('на руки, в месяц')).toBeInTheDocument()
  })

  it('opens the profile once the first resume is saved', async () => {
    signIn('candidate')
    // `/candidates/me` answers null until the first save, the profile after it.
    let profile: OwnCandidateDto | null = null
    const rest = mockFetch({
      '/api/v1/categories/dictionary': {
        body: { specializations: [{ code: 'backend', label: 'Backend-разработка' }], grades: [] },
      },
      '/api/v1/cities/search': {
        body: [
          {
            id: 551487,
            name: 'Казань',
            countryCode: 'RU',
            region: 'Татарстан',
            latitude: 55.7887,
            longitude: 49.1221,
          },
        ],
      },
    })
    vi.stubGlobal('fetch', async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = new URL(String(input), 'http://localhost')
      if (url.pathname !== '/api/v1/candidates/me') return rest(input)
      if (init?.method === 'PATCH') profile = SAVED_RESUME
      return new Response(JSON.stringify(profile), {
        headers: { 'Content-Type': 'application/json' },
      })
    })
    renderApp('/profile/resume')
    const user = userEvent.setup()

    const manual = await screen.findByRole('button', { name: 'Заполнить вручную' }, SLOW)
    // While the resume is missing, the sections of the cabinet are closed and not shown.
    expect(screen.queryByRole('link', { name: 'Приглашения' })).not.toBeInTheDocument()
    await user.click(screen.getByLabelText('Позже'))
    await user.click(manual)

    await user.type(screen.getByLabelText('Имя и фамилия'), 'Анна Петрова')
    await user.type(screen.getByLabelText('Должность'), 'Backend-разработчик')
    await user.selectOptions(await screen.findByLabelText('Специализация'), 'backend')
    // The city is picked from the directory, not typed: `cityId` is what the form saves.
    await user.type(screen.getByLabelText('Город'), 'Казань')
    await user.click(await screen.findByRole('option', { name: 'Казань' }, SLOW))
    await user.type(screen.getByLabelText('Стаж, лет'), '3')
    await user.click(screen.getByLabelText('Удалённо'))
    await user.click(screen.getByLabelText('Полная'))
    for (const skill of ['Python', 'PostgreSQL', 'Docker']) {
      await user.click(screen.getByRole('button', { name: skill }))
    }
    await user.type(screen.getByLabelText('Telegram'), '@anna')
    await user.click(screen.getByRole('button', { name: 'Сохранить резюме' }))

    // The form gives way to the profile as the employer sees it, with the cabinet around it.
    expect(await screen.findByText(/Так вас видит работодатель/, {}, SLOW)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Обзор' })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Приглашения' })).not.toBeInTheDocument()
    expect(screen.queryByText(/создать ещё одно резюме/)).not.toBeInTheDocument()
    // The next step is offered in a window over the profile.
    const next = screen.getByRole('dialog', { name: 'Резюме сохранено' })
    expect(next).toHaveTextContent('Следующий шаг — тест')
    await user.click(screen.getByRole('button', { name: 'Позже' }))
    expect(screen.queryByRole('dialog', { name: 'Резюме сохранено' })).not.toBeInTheDocument()
  })

  it('asks an employer about themselves before the company', async () => {
    signIn('employer')
    vi.stubGlobal('fetch', mockFetch(NO_COMPANY))
    const { router } = renderApp('/feed/swipe')
    await waitFor(() => expect(router.state.location.pathname).toBe('/profile/company'), SLOW)
    expect(await screen.findByLabelText('Имя', {}, SLOW)).toBeInTheDocument()
    expect(screen.getByLabelText('Фамилия')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Настройка компании' })).toBeInTheDocument()
    expect(screen.getByText(/остальные разделы закрыты/)).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Свайпы' })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Далее' })).toBeInTheDocument()
  })

  it('checks the INN before the company profile step', async () => {
    signIn('employer', { firstName: 'Анна', lastName: 'Петрова' })
    vi.stubGlobal('fetch', mockFetch(NO_COMPANY))
    renderApp('/profile/company')
    const user = userEvent.setup()

    const inn = await screen.findByLabelText('ИНН', {}, SLOW)
    expect(screen.getByText(/Автозаполнение по ИНН — в разработке/)).toBeInTheDocument()
    await user.type(inn, '1234567890')
    await user.click(screen.getByRole('button', { name: 'Далее' }))
    expect(await screen.findByText(/ИНН/, { selector: '.field__error' })).toBeInTheDocument()

    await user.clear(inn)
    await user.type(inn, '7707083893')
    await user.click(screen.getByRole('button', { name: 'Далее' }))
    expect(await screen.findByLabelText('Название для кандидатов', {}, SLOW)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Сохранить и продолжить' })).toBeInTheDocument()
  })

  it('keeps the setup on the logo step once the company is saved', async () => {
    signIn('employer', { firstName: 'Анна', lastName: 'Петрова' })
    // `/companies/me` answers null until the save, the company after it.
    let company: unknown = null
    const rest = mockFetch({})
    vi.stubGlobal('fetch', async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = new URL(String(input), 'http://localhost')
      if (url.pathname !== '/api/v1/companies/me') return rest(input)
      if (init?.method && init.method !== 'GET') {
        company = { id: 'co', ...(JSON.parse(String(init.body)) as object) }
      }
      return new Response(JSON.stringify(company), {
        headers: { 'Content-Type': 'application/json' },
      })
    })
    const { router } = renderApp('/profile/company')
    const user = userEvent.setup()

    await user.type(await screen.findByLabelText('ИНН', {}, SLOW), '7707083893')
    await user.click(screen.getByRole('button', { name: 'Далее' }))
    await user.type(await screen.findByLabelText('Название для кандидатов', {}, SLOW), 'Технологии')
    await user.selectOptions(screen.getByLabelText('Направление деятельности'), 'Финтех')
    await user.type(screen.getByLabelText('Город'), 'Казань')
    await user.type(screen.getByLabelText('Сайт'), 'company.ru')
    await user.type(screen.getByLabelText('Контакт для кандидатов'), 'hr@company.ru')
    await user.click(screen.getByLabelText('Описание'))
    await user.paste('Мы делаем платёжные сервисы. '.repeat(5))
    await user.click(screen.getByRole('button', { name: 'Сохранить и продолжить' }))

    // The saved company opens the sections only after the last step of the setup.
    const done = await screen.findByRole('button', { name: 'Перейти в кабинет' }, SLOW)
    expect(screen.getByRole('heading', { name: 'Настройка компании' })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Приглашения' })).not.toBeInTheDocument()
    await user.click(done)
    await waitFor(() => expect(router.state.location.pathname).toBe('/profile'), SLOW)
    expect(await screen.findByRole('link', { name: 'Обзор' }, SLOW)).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Приглашения' })).not.toBeInTheDocument()
  })
})
