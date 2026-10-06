import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it } from 'vitest'
import type {
  AssessmentAttemptDto,
  AssessmentStatusDto,
  AttemptDetailDto,
} from '@/entities/assessment'
import { sessionStore } from '@/entities/session'
import { renderApp, stubApi } from './test-utils'

// The first render loads the lazy page chunk, which can take longer than the default 1 s.
const SLOW = { timeout: 5000 }

const attemptBase: AssessmentAttemptDto = {
  id: 'a1',
  assignmentId: null,
  title: 'Backend-разработка · Junior',
  specialization: 'backend',
  grade: 'junior',
  status: 'in_progress',
  score: null,
  passScore: 60,
  startedAt: new Date().toISOString(),
  expiresAt: new Date(Date.now() + 25 * 60_000).toISOString(),
  finishedAt: null,
  breakdown: null,
}

const attempt: Omit<AttemptDetailDto, 'clockOffset'> = {
  ...attemptBase,
  runsLeft: 20,
  serverTime: new Date().toISOString(),
  tasks: [
    {
      id: 't1',
      kind: 'quiz',
      topic: 'sql',
      difficulty: 'easy',
      title: 'Что делает индекс?',
      statement: 'Что делает индекс?',
      content: { options: ['Ускоряет поиск', 'Шифрует таблицу'], multiple: false },
      answer: { selected: [0] },
    },
  ],
}

const status: AssessmentStatusDto = {
  status: 'not_taken',
  specialization: null,
  grade: null,
  score: null,
  nextAttemptAt: null,
  tracks: [],
  activeAttemptId: null,
  codeRunnerAvailable: true,
  history: [],
}

/** The candidate is in the middle of a test; `finish` answers with the given result. */
function takeTest(result: Partial<AssessmentAttemptDto>) {
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
  return stubApi(({ method, path }, before) => {
    const finished = before.some((call) => call.path.endsWith('/finish'))
    if (path === '/assessments/me') return { ...status, activeAttemptId: finished ? null : 'a1' }
    if (path === '/assessments/attempts/a1') return attempt
    if (path === '/assessments/attempts/a1/finish')
      return { ...attemptBase, finishedAt: new Date().toISOString(), ...result }
    if (path === '/categories/dictionary')
      return {
        specializations: [{ code: 'backend', label: 'Backend-разработка' }],
        grades: [
          { code: 'junior', label: 'Junior' },
          { code: 'middle', label: 'Middle' },
        ],
      }
    return method === 'GET' ? [] : undefined
  })
}

async function finishTest() {
  const user = userEvent.setup()
  renderApp('/testing')
  await user.click(await screen.findByRole('button', { name: 'Завершить тест' }, SLOW))
  await user.click(screen.getByRole('button', { name: 'Да, завершить' }))
  return user
}

describe('result of a finished attempt', () => {
  afterEach(() => sessionStore.clear())

  it('recommends the next grade after a strong result and puts it into the form', async () => {
    takeTest({ status: 'passed', score: 92, recommendedGrade: 'middle' })

    const user = await finishTest()

    expect(await screen.findByText('Тест пройден — категория подтверждена')).toBeInTheDocument()
    expect(screen.getByText(/рекомендуем тест на Middle/)).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Выбрать этот тест' }))

    await waitFor(() =>
      expect(screen.getByLabelText('Грейд, на который претендуете')).toHaveValue('middle'),
    )
    expect(screen.getByLabelText('Специализация')).toHaveValue('backend')
  })

  it('does not recommend anything after an ordinary pass', async () => {
    takeTest({ status: 'passed', score: 70, recommendedGrade: null })

    await finishTest()

    expect(await screen.findByText('Тест пройден — категория подтверждена')).toBeInTheDocument()
    expect(screen.queryByText(/рекомендуем тест/)).not.toBeInTheDocument()
  })

  it('tells that the solution is still being checked when the code runner is down', async () => {
    takeTest({ status: 'grading', score: null })

    await finishTest()

    expect(await screen.findByText('Проверяем решение')).toBeInTheDocument()
    expect(screen.getByText(/пауза за это время не начисляется/)).toBeInTheDocument()
    expect(screen.queryByText('Тест не пройден')).not.toBeInTheDocument()
  })
})
