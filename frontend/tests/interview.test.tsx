import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it } from 'vitest'
import type { AssessmentStatusDto, InterviewDto } from '@/entities/assessment'
import { sessionStore } from '@/entities/session'
import { renderApp, stubApi } from './test-utils'

// The first render loads the lazy page chunk, which can take longer than the default 1 s.
const SLOW = { timeout: 5000 }

const waiting: AssessmentStatusDto = {
  status: 'not_taken',
  specialization: null,
  grade: null,
  score: null,
  nextAttemptAt: null,
  tracks: [],
  activeAttemptId: null,
  interviewAttemptId: 'a1',
  codeRunnerAvailable: true,
  history: [],
}

const asked: InterviewDto = {
  attemptId: 'a1',
  status: 'asked',
  questions: [
    { number: 1, taskTitle: 'Частые IP', text: 'Почему здесь куча, а не сортировка?' },
    { number: 2, taskTitle: 'Частые IP', text: 'Что будет на огромном логе?' },
  ],
  deadline: new Date(Date.now() + 15 * 60_000).toISOString(),
  result: null,
}

describe('AI interview after a grade test', () => {
  afterEach(() => sessionStore.clear())

  it('sends the answers about the code and shows the confirmed grade', async () => {
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
    const calls = stubApi(({ method, path }) => {
      if (path === '/candidates/me') return { id: 'me' }
      if (path === '/assessments/me') return waiting
      if (path !== '/assessments/attempts/a1/interview') return undefined
      if (method === 'GET') return asked
      return {
        ...asked,
        status: 'passed',
        deadline: null,
        result: {
          score: 85,
          passScore: 60,
          passed: true,
          summary: 'Вы хорошо объяснили своё решение.',
          marks: [
            { number: 1, score: 90, comment: 'По делу' },
            { number: 2, score: 80, comment: '' },
          ],
        },
      }
    })
    const user = userEvent.setup()

    renderApp('/testing')
    await user.type(
      await screen.findByRole('textbox', { name: 'Ответ на вопрос 1' }, SLOW),
      'Куча держит только k адресов',
    )
    await user.type(screen.getByRole('textbox', { name: 'Ответ на вопрос 2' }), 'Читать построчно')
    await user.click(screen.getByRole('button', { name: 'Отправить ответы' }))

    expect(
      await screen.findByText('Понимание кода подтверждено — грейд подтверждён'),
    ).toBeInTheDocument()
    const sent = calls.find((call) => call.method === 'POST' && call.path.endsWith('/interview'))
    expect(sent?.body).toEqual({ answers: ['Куча держит только k адресов', 'Читать построчно'] })
  })
})
