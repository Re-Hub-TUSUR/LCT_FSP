import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type {
  AssessmentAttemptDto,
  AssessmentStatusDto,
  AssignmentDetailDto,
  AssignmentDto,
  AttemptDetailDto,
} from '@/entities/assessment'
import { sessionStore } from '@/entities/session'
import type { UserRole } from '@/entities/user'
import { renderApp } from './test-utils'

// The first render loads the lazy page chunk, which can take longer than the default 1 s.
const SLOW = { timeout: 5000 }
const API = '/api/v1'

function signIn(role: UserRole) {
  sessionStore.set({
    accessToken: 't',
    user: { id: 'u1', email: 'u@fsp.ru', role, isEmailVerified: true, createdAt: '2026-01-01' },
  })
}

type Call = { method: string; path: string; body: unknown }

/** A `fetch` whose answers may depend on what was called before. */
function stubApi(answer: (call: Call, calls: Call[]) => unknown) {
  const calls: Call[] = []
  vi.stubGlobal('fetch', async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = new URL(typeof input === 'string' ? input : input.toString(), 'http://localhost')
    const call: Call = {
      method: init?.method ?? 'GET',
      path: url.pathname.replace(API, ''),
      body: init?.body ? JSON.parse(String(init.body)) : undefined,
    }
    const body = answer(call, calls)
    calls.push(call)
    return new Response(body === undefined ? null : JSON.stringify(body), {
      status: body === undefined ? 204 : 200,
      headers: { 'Content-Type': 'application/json' },
    })
  })
  return calls
}

const assignment: AssignmentDto = {
  id: 'as1',
  title: 'Тестовое в команду платежей',
  status: 'sent',
  company: { id: 'c1', name: 'ПэйФлоу' },
  candidate: { id: 'p1', name: 'Марина Крылова' },
  vacancy: null,
  message: 'Ждём до пятницы',
  durationMinutes: 40,
  tasksCount: 2,
  createdAt: '2026-10-07T10:00:00Z',
  dueAt: '2026-10-14T20:59:00Z',
  attemptId: null,
  finishedAt: null,
  score: null,
  passScore: null,
}

const attemptBase: AssessmentAttemptDto = {
  id: 'a1',
  assignmentId: 'as1',
  title: assignment.title,
  specialization: null,
  grade: null,
  status: 'in_progress',
  score: null,
  passScore: 60,
  startedAt: new Date().toISOString(),
  expiresAt: new Date(Date.now() + 40 * 60_000).toISOString(),
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
      topic: 'team',
      difficulty: 'easy',
      title: 'Какой у нас стек?',
      statement: 'Какой у нас стек?',
      content: { options: ['Python', 'COBOL'], multiple: false },
      answer: null,
    },
    {
      id: 't2',
      kind: 'open',
      topic: 'design',
      difficulty: 'medium',
      title: 'Очередь задач',
      statement: 'Опишите, как вы спроектируете очередь задач.',
      content: { maxLength: 500 },
      answer: null,
    },
  ],
}

const emptyStatus: AssessmentStatusDto = {
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

describe('test assignments', () => {
  afterEach(() => sessionStore.clear())

  it('gives the employer a separate page for building tests', async () => {
    signIn('employer')
    stubApi(({ method, path }) => {
      if (path === '/companies/me/assessment-tasks')
        return { items: [], total: 0, page: 1, perPage: 10, pages: 0 }
      return method === 'GET' ? [] : undefined
    })
    const user = userEvent.setup()

    renderApp('/testing')
    await user.click(await screen.findByRole('link', { name: 'Конструктор тестов →' }, SLOW))

    expect(
      await screen.findByRole('heading', { name: 'Конструктор тестов' }, SLOW),
    ).toBeInTheDocument()
    expect(await screen.findByText('В банке пока нет задач')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Добавить открытый вопрос' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Добавить тест' })).toBeInTheDocument()
  })

  it('keeps the test builder away from candidates', async () => {
    signIn('candidate')
    stubApi(({ method }) => (method === 'GET' ? [] : undefined))

    renderApp('/testing/builder')

    expect(await screen.findByText('Нет доступа', {}, SLOW)).toBeInTheDocument()
  })

  it('lets a candidate take a company test with an open question', async () => {
    signIn('candidate')
    const calls = stubApi(({ method, path }, before) => {
      const started = before.some((call) => call.path.endsWith('/start'))
      const finished = before.some((call) => call.path.endsWith('/finish'))
      if (path === '/assessments/me')
        return { ...emptyStatus, activeAttemptId: started && !finished ? 'a1' : null }
      if (path === '/assessments/assignments')
        return [{ ...assignment, status: finished ? 'review' : started ? 'in_progress' : 'sent' }]
      if (path === '/assessments/assignments/as1/start' || path === '/assessments/attempts/a1')
        return attempt
      if (path === '/assessments/attempts/a1/finish')
        return { ...attemptBase, status: 'awaiting_review', finishedAt: new Date().toISOString() }
      if (path === '/assessments/templates') return []
      if (path === '/categories/dictionary') return { specializations: [], grades: [] }
      return method === 'GET' ? [] : undefined
    })
    const user = userEvent.setup()

    renderApp('/testing')
    expect(await screen.findByText('Ждём до пятницы', {}, SLOW)).toBeInTheDocument()
    expect(screen.getByText(/40 минут · заданий: 2/)).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Начать' }))
    await user.click(await screen.findByLabelText('Python'))
    await user.click(screen.getByRole('button', { name: 'Далее' }))
    await user.type(screen.getByLabelText('Ваш ответ'), 'Очередь с ретраями')
    expect(screen.getByText(/18 из 500 символов/)).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Завершить тест' }))
    await user.click(screen.getByRole('button', { name: 'Да, завершить' }))

    expect(await screen.findByText('Ответы отправлены')).toBeInTheDocument()
    expect(await screen.findByText(/компания проверяет открытые вопросы/)).toBeInTheDocument()
    const saved = calls.filter((call) => call.path === '/assessments/attempts/a1/answers')
    // The choice is saved at once; the typed text — in one piece before finishing.
    expect(saved.map((call) => call.body)).toEqual([
      { taskId: 't1', answer: { selected: [0] } },
      { taskId: 't2', answer: { text: 'Очередь с ретраями' } },
    ])
  })

  it('lets an employer grade the open answer of a taken test', async () => {
    signIn('employer')
    const taken: AssignmentDetailDto = {
      ...assignment,
      status: 'review',
      attemptId: 'a1',
      finishedAt: '2026-10-08T12:00:00Z',
      passScore: 60,
      pasteCount: 2,
      blurCount: 0,
      tasks: [
        {
          id: 't1',
          kind: 'quiz',
          title: 'Какой у нас стек?',
          statement: 'Какой у нас стек?',
          answered: true,
          points: 1,
          manual: false,
          comment: null,
          review: { options: ['Python', 'COBOL'], correct: [0], selected: [0] },
        },
        {
          id: 't2',
          kind: 'open',
          title: 'Очередь задач',
          statement: 'Опишите, как вы спроектируете очередь задач.',
          answered: true,
          points: null,
          manual: true,
          comment: null,
          review: { text: 'Очередь с ретраями', guidance: 'Ретраи, идемпотентность' },
        },
      ],
    }
    const calls = stubApi(({ method, path }) => {
      if (path === '/companies/me/test-assignments') return [taken]
      if (path === '/companies/me/test-assignments/as1') return taken
      if (path === '/companies/me/test-assignments/as1/review')
        return {
          ...taken,
          status: 'done',
          score: 75,
          tasks: taken.tasks.map((task) => (task.manual ? { ...task, points: 0.5 } : task)),
        }
      return method === 'GET' ? [] : undefined
    })
    const user = userEvent.setup()

    renderApp('/testing')
    const row = (await screen.findByRole('link', { name: 'Марина Крылова' }, SLOW)).closest('tr')!
    expect(within(row).getByText('Ждёт проверки')).toBeInTheDocument()

    await user.click(within(row).getByRole('button', { name: 'Проверить' }))
    expect(await screen.findByText('Очередь с ретраями')).toBeInTheDocument()
    expect(screen.getByText(/На что смотреть: Ретраи, идемпотентность/)).toBeInTheDocument()
    expect(screen.getByText(/Вставок из буфера: 2/)).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Сохранить оценки' }))
    expect(screen.getByText('Оцените каждый открытый ответ: от 0 до 100')).toBeInTheDocument()

    await user.type(screen.getByLabelText('Оценка, % от задания'), '50')
    await user.type(screen.getByLabelText('Комментарий'), 'Нет про мониторинг')
    await user.click(screen.getByRole('button', { name: 'Сохранить оценки' }))

    expect(await screen.findByText(/Итог: 75 из 100/)).toBeInTheDocument()
    await waitFor(() => expect(calls.some((call) => call.method === 'PUT')).toBe(true))
    expect(calls.find((call) => call.method === 'PUT')?.body).toEqual({
      grades: [{ taskId: 't2', points: 0.5, comment: 'Нет про мониторинг' }],
    })
  })
})
