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
      // A strong result opened Senior: no wait for the cooldown above.
      recommendation: { grade: 'senior', nextAttemptAt: null },
    },
    {
      specialization: 'frontend',
      status: 'passed',
      grade: 'junior',
      score: 71,
      nextAttemptAt: null,
      isPrimary: false,
      recommendation: null,
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
    recommendScore: 85,
  },
  {
    grade: 'junior',
    specialization: 'qa',
    durationMinutes: 40,
    passScore: 70,
    tasks: { quiz: 12 },
    retryDays: 1,
    gradeChangeDays: 30,
    recommendScore: 90,
  },
  {
    grade: 'senior',
    specialization: null,
    durationMinutes: 35,
    passScore: 60,
    tasks: { quiz: 12 },
    retryDays: 7,
    gradeChangeDays: 90,
    recommendScore: 85,
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
    { code: 'senior', label: 'Senior' },
  ],
}

function signIn() {
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
}

function stubFetch(own?: { status?: AssessmentStatusDto; templates?: AssessmentTemplateDto[] }) {
  const fetchMock = vi.fn<typeof fetch>(
    mockFetch({
      '/api/v1/assessments/me': { body: own?.status ?? status },
      '/api/v1/assessments/templates': { body: own?.templates ?? templates },
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
    signIn()
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
    signIn()
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
    expect(screen.getByText(/При результате от 90 из 100 тест на Middle/)).toBeInTheDocument()
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

  it('opens the recommended next grade without the grade-change pause', async () => {
    signIn()
    stubFetch()
    const user = userEvent.setup()

    renderApp('/testing')
    const specialization = await screen.findByLabelText('Специализация', {}, SLOW)
    const grade = screen.getByLabelText('Грейд, на который претендуете')
    const startButton = screen.getByRole('button', { name: 'Начать тест' })

    // The form opens on what the primary category recommends.
    await waitFor(() => expect(specialization).toHaveValue('backend'))
    expect(grade).toHaveValue('senior')
    expect(
      await screen.findByText(/рекомендован по итогам вашего прошлого теста/),
    ).toBeInTheDocument()
    expect(startButton).toBeEnabled()

    // Any other grade of the same specialization still waits.
    await user.selectOptions(grade, 'junior')
    expect(screen.getByText(/следующая попытка будет доступна/)).toBeInTheDocument()
    expect(startButton).toBeDisabled()

    await user.click(screen.getByRole('button', { name: 'Рекомендуем Senior' }))
    await waitFor(() =>
      expect(screen.getByLabelText('Грейд, на который претендуете')).toHaveValue('senior'),
    )
    expect(screen.getByRole('button', { name: 'Начать тест' })).toBeEnabled()
  })

  it('opens a lower grade at once after a failure and states the quiz minimum and the beta', async () => {
    signIn()
    stubFetch({
      status: {
        ...status,
        status: 'failed',
        specialization: null,
        grade: null,
        score: null,
        nextAttemptAt: '2027-01-10T10:00:00Z',
        tracks: [
          {
            specialization: 'qa',
            status: 'failed',
            grade: null,
            score: null,
            nextAttemptAt: '2027-01-10T10:00:00Z',
            isPrimary: false,
            recommendation: null,
            failedGrade: 'senior',
          },
        ],
      },
      templates: [
        { ...templates[2]!, quizMin: 50, isBeta: true },
        { ...templates[0]!, tasks: { quiz: 10 } },
      ],
    })
    const user = userEvent.setup()

    renderApp('/testing')
    const specialization = await screen.findByLabelText('Специализация', {}, SLOW)
    const grade = screen.getByLabelText('Грейд, на который претендуете')
    const startButton = screen.getByRole('button', { name: 'Начать тест' })
    await user.selectOptions(specialization, 'qa')

    // The failed grade waits; its rules name the quiz minimum and the beta mark.
    await user.selectOptions(grade, 'senior')
    expect(await screen.findByText(/не менее чем на 50% вопросов/)).toBeInTheDocument()
    expect(screen.getByText(/Тест в бета-версии/)).toBeInTheDocument()
    expect(screen.getByText(/следующая попытка будет доступна/)).toBeInTheDocument()
    expect(startButton).toBeDisabled()

    // A lower grade is open without the pause.
    await user.selectOptions(grade, 'junior')
    expect(await screen.findByText(/можно пройти сразу, без паузы/)).toBeInTheDocument()
    expect(screen.queryByText(/следующая попытка будет доступна/)).not.toBeInTheDocument()
    expect(startButton).toBeEnabled()
  })
})
