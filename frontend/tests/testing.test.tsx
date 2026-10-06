import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { AssessmentStatusDto, AssessmentTemplateDto } from '@/entities/assessment'
import { sessionStore } from '@/entities/session'
import { mockFetch, renderApp } from './test-utils'

// The first render loads the lazy page chunk, which can take longer than the default 1 s.
const SLOW = { timeout: 5000 }

const status: AssessmentStatusDto = {
  status: 'passed',
  specialization: 'backend',
  grade: 'middle',
  score: 82,
  nextAttemptAt: '2027-01-10T10:00:00Z',
  tracks: [
    {
      specialization: 'backend',
      status: 'passed',
      grade: 'middle',
      score: 82,
      nextAttemptAt: '2027-01-10T10:00:00Z',
      isPrimary: true,
    },
    {
      specialization: 'frontend',
      status: 'passed',
      grade: 'junior',
      score: 71,
      nextAttemptAt: null,
      isPrimary: false,
    },
  ],
  activeAttemptId: null,
  codeRunnerAvailable: false,
  history: [],
}

const templates: AssessmentTemplateDto[] = [
  {
    grade: 'junior',
    specialization: null,
    durationMinutes: 25,
    passScore: 60,
    tasks: { quiz: 10, code: 1 },
    retryDays: 7,
    gradeChangeDays: 90,
  },
  {
    grade: 'junior',
    specialization: 'qa',
    durationMinutes: 40,
    passScore: 70,
    tasks: { quiz: 12 },
    retryDays: 1,
    gradeChangeDays: 30,
  },
]

const dictionary = {
  specializations: [
    { code: 'backend', label: 'Backend-разработка' },
    { code: 'frontend', label: 'Frontend-разработка' },
    { code: 'qa', label: 'Тестирование (QA)' },
  ],
  grades: [
    { code: 'junior', label: 'Junior' },
    { code: 'middle', label: 'Middle' },
  ],
}

function stubFetch() {
  const fetchMock = vi.fn<typeof fetch>(
    mockFetch({
      '/api/v1/assessments/me': { body: status },
      '/api/v1/assessments/templates': { body: templates },
      '/api/v1/categories/dictionary': { body: dictionary },
      '/api/v1/assessments/me/primary': {
        body: {
          ...status,
          specialization: 'frontend',
          tracks: status.tracks.map((track) => ({ ...track, isPrimary: !track.isPrimary })),
        },
      },
    }),
  )
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

describe('testing page', () => {
  afterEach(() => sessionStore.clear())

  it('lists the categories and lets the candidate choose the primary one', async () => {
    sessionStore.set({
      accessToken: 't',
      user: {
        id: 'u1',
        email: 'u@fsp.ru',
        role: 'candidate',
        isEmailVerified: true,
        createdAt: '2026-01-01',
      },
    })
    const fetchMock = stubFetch()
    const user = userEvent.setup()

    renderApp('/testing')
    const frontend = (await screen.findByRole('cell', { name: 'Frontend-разработка' }, SLOW))
      .parentElement!
    const backend = screen.getByRole('cell', { name: 'Backend-разработка' }).parentElement!

    expect(within(backend).getByText('Основная')).toBeInTheDocument()
    expect(within(backend).getByText('10 января 2027 г.')).toBeInTheDocument()
    expect(within(frontend).getByText('Доступна')).toBeInTheDocument()

    await user.click(within(frontend).getByRole('button', { name: 'Сделать основной' }))

    await waitFor(() => expect(within(frontend).getByText('Основная')).toBeInTheDocument())
    const put = fetchMock.mock.calls.find(([, init]) => init?.method === 'PUT')
    expect(JSON.parse(String(put?.[1]?.body))).toEqual({ specialization: 'frontend' })
  })

  it('shows the real rules of the chosen test and what blocks the start', async () => {
    sessionStore.set({
      accessToken: 't',
      user: {
        id: 'u1',
        email: 'u@fsp.ru',
        role: 'candidate',
        isEmailVerified: true,
        createdAt: '2026-01-01',
      },
    })
    stubFetch()
    const user = userEvent.setup()

    renderApp('/testing')
    const specialization = await screen.findByLabelText('Специализация', {}, SLOW)
    const grade = screen.getByLabelText('Грейд, на который претендуете')
    const startButton = screen.getByRole('button', { name: 'Начать тест' })

    // The template of the specialization wins over the general one of the grade.
    await user.selectOptions(specialization, 'qa')
    await user.selectOptions(grade, 'junior')
    expect(await screen.findByText(/Тест идёт 40 минут/)).toBeInTheDocument()
    expect(screen.getByText(/Проходной балл — 70 из 100/)).toBeInTheDocument()
    expect(startButton).toBeEnabled()

    // The general junior test has a code task, and the runner is down.
    await user.selectOptions(specialization, 'frontend')
    expect(screen.getByText(/Тест идёт 25 минут/)).toBeInTheDocument()
    expect(screen.getByText(/Проверка кода сейчас недоступна/)).toBeInTheDocument()
    expect(startButton).toBeDisabled()

    // Backend is on its own cooldown.
    await user.selectOptions(specialization, 'backend')
    expect(screen.getByText(/следующая попытка будет доступна/)).toBeInTheDocument()
    expect(startButton).toBeDisabled()
  })
})
