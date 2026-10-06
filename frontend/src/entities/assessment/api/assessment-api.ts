import { queryOptions } from '@tanstack/react-query'
import { http } from '@/shared/api'
import type { Paginated } from '@/shared/api'

/** What an employer sees about the platform grade test. */
export type AssessmentStatus = 'not_taken' | 'passed' | 'failed'

export type AssessmentAttemptStatus = 'in_progress' | 'passed' | 'failed' | 'expired'

export type TaskKind = 'quiz' | 'code'
export type TaskDifficulty = 'easy' | 'medium' | 'hard'
export type Verdict = 'ok' | 'wrong_answer' | 'runtime_error' | 'time_limit'

export type TopicResultDto = {
  topic: string
  kind: TaskKind
  /** Share of the topic's tasks earned, 0..1. */
  earned: number
  total: number
}

export type AssessmentAttemptDto = {
  id: string
  title: string
  specialization: string | null
  grade: string | null
  status: AssessmentAttemptStatus
  score: number | null
  passScore: number
  startedAt: string
  expiresAt: string
  finishedAt: string | null
  breakdown: TopicResultDto[] | null
}

export type CodeAnswerDto = { language: string; code: string }

/** Candidate view of a task: never carries correct options or hidden tests. */
export type AttemptTaskDto = {
  id: string
  kind: TaskKind
  topic: string
  difficulty: TaskDifficulty
  title: string
  statement: string
  options: string[] | null
  multiple: boolean | null
  selected: number[] | null
  languages: { id: string; label: string }[] | null
  timeLimit: number | null
  samples: { input: string; expected: string }[] | null
  draft: CodeAnswerDto | null
}

export type AttemptDetailDto = AssessmentAttemptDto & {
  tasks: AttemptTaskDto[]
  runsLeft: number
  /** Server clock at response time: the countdown must not trust the device clock. */
  serverTime: string
  /**
   * Server "now" minus device "now", measured when the response arrived. Added on the client:
   * taken later (e.g. from cached data) it would wind the countdown back.
   */
  clockOffset: number
}

const withClockOffset = (attempt: Omit<AttemptDetailDto, 'clockOffset'>): AttemptDetailDto => ({
  ...attempt,
  clockOffset: Date.parse(attempt.serverTime) - Date.now(),
})

export type RunResultDto = {
  /** Null for a run on the candidate's own input. */
  verdict: Verdict | null
  input: string
  expected: string | null
  output: string
  error: string
  time: number | null
}

export type RunResponseDto = { results: RunResultDto[]; runsLeft: number }

/** Candidate's categorisation state and what they may do next. */
export type AssessmentStatusDto = {
  status: AssessmentStatus
  specialization: string | null
  grade: string | null
  score: number | null
  activeAttemptId: string | null
  /** Null = a new attempt may start right now. */
  nextAttemptAt: string | null
  /** False until the code runner key is configured on the server. */
  codeRunnerAvailable: boolean
  history: AssessmentAttemptDto[]
}

export type AnswerPayload =
  { taskId: string; selected: number[] } | ({ taskId: string } & CodeAnswerDto)

export const assessmentKeys = {
  all: ['assessments'] as const,
  status: () => [...assessmentKeys.all, 'status'] as const,
  attempt: (id: string) => [...assessmentKeys.all, 'attempt', id] as const,
}

export const assessmentQueries = {
  status: () =>
    queryOptions({
      queryKey: assessmentKeys.status(),
      queryFn: ({ signal }) => http.get<AssessmentStatusDto>('/assessments/me', { signal }),
    }),
  attempt: (id: string) =>
    queryOptions({
      queryKey: assessmentKeys.attempt(id),
      queryFn: ({ signal }) =>
        http.get<AttemptDetailDto>(`/assessments/attempts/${id}`, { signal }).then(withClockOffset),
      // The runner keeps answers locally, so a background refetch would only fight with them.
      // The runner drops this entry when it closes: coming back always loads the saved state.
      staleTime: Infinity,
    }),
}

export const assessmentApi = {
  start: (payload: { specialization: string; grade: string }) =>
    http.post<AttemptDetailDto>('/assessments/attempts', payload).then(withClockOffset),
  saveAnswer: (attemptId: string, payload: AnswerPayload) =>
    http.post<void>(`/assessments/attempts/${attemptId}/answers`, payload),
  run: (attemptId: string, payload: { taskId: string; input?: string } & CodeAnswerDto) =>
    http.post<RunResponseDto>(`/assessments/attempts/${attemptId}/run`, payload),
  signal: (attemptId: string, kind: 'paste' | 'blur') =>
    http.post<void>(`/assessments/attempts/${attemptId}/signals`, { kind }),
  finish: (attemptId: string) =>
    http.post<AssessmentAttemptDto>(`/assessments/attempts/${attemptId}/finish`),
}

// ── Task bank (authors: admin for the platform bank, employer for their own) ────────────────

export type BankScope = 'admin' | 'employer'

export type QuizPayloadDto = { options: string[]; correct: number[]; multiple: boolean }

export type TestGroupDto = { input: string; expected: string; hidden: boolean }

export type CodePayloadDto = {
  languages: string[]
  timeLimit: number
  groups: TestGroupDto[]
  reference: CodeAnswerDto | null
}

export type BankTaskWrite = {
  kind: TaskKind
  difficulty: TaskDifficulty
  specializations: string[]
  topic: string
  title: string
  statement: string
  quiz: QuizPayloadDto | null
  code: CodePayloadDto | null
  isActive: boolean
}

export type BankTaskDto = BankTaskWrite & { id: string; platform: boolean; createdAt: string }

export type CompositionRuleDto = {
  kind: TaskKind
  count: number
  difficulty: TaskDifficulty[]
  topics: string[]
  scope: 'specialization' | 'general' | 'any'
}

export type CompositionDto =
  { mode: 'rules'; rules: CompositionRuleDto[] } | { mode: 'fixed'; taskIds: string[] }

export type BankTestWrite = {
  title: string
  grade: string | null
  durationMinutes: number
  passScore: number
  quizWeight: number
  composition: CompositionDto
  isActive: boolean
}

export type BankTestDto = BankTestWrite & { id: string; platform: boolean; createdAt: string }

export type TaskCheckDto = {
  ok: boolean
  groups: {
    hidden: boolean
    verdict: Verdict
    output: string
    error: string
    time: number | null
  }[]
}

const BANK_ROOT: Record<BankScope, string> = { admin: '/admin', employer: '/companies/me' }

export const bankKeys = {
  all: (scope: BankScope) => ['assessment-bank', scope] as const,
  tasks: (scope: BankScope) => [...bankKeys.all(scope), 'tasks'] as const,
  tests: (scope: BankScope) => [...bankKeys.all(scope), 'tests'] as const,
}

export const bankQueries = {
  tasks: (scope: BankScope) =>
    queryOptions({
      queryKey: bankKeys.tasks(scope),
      queryFn: ({ signal }) =>
        http.get<Paginated<BankTaskDto>>(`${BANK_ROOT[scope]}/assessment-tasks`, {
          signal,
          query: { perPage: 100 },
        }),
    }),
  tests: (scope: BankScope) =>
    queryOptions({
      queryKey: bankKeys.tests(scope),
      queryFn: ({ signal }) =>
        http.get<BankTestDto[]>(`${BANK_ROOT[scope]}/assessment-tests`, { signal }),
    }),
}

export const bankApi = {
  /** Without `id` the task is created, with it — replaced. */
  saveTask: (scope: BankScope, payload: BankTaskWrite, id?: string) =>
    id
      ? http.put<BankTaskDto>(`${BANK_ROOT[scope]}/assessment-tasks/${id}`, payload)
      : http.post<BankTaskDto>(`${BANK_ROOT[scope]}/assessment-tasks`, payload),
  deleteTask: (scope: BankScope, id: string) =>
    http.delete<void>(`${BANK_ROOT[scope]}/assessment-tasks/${id}`),
  checkTask: (scope: BankScope, id: string) =>
    http.post<TaskCheckDto>(`${BANK_ROOT[scope]}/assessment-tasks/${id}/check`),
  saveTest: (scope: BankScope, payload: BankTestWrite, id?: string) =>
    id
      ? http.put<BankTestDto>(`${BANK_ROOT[scope]}/assessment-tests/${id}`, payload)
      : http.post<BankTestDto>(`${BANK_ROOT[scope]}/assessment-tests`, payload),
  deleteTest: (scope: BankScope, id: string) =>
    http.delete<void>(`${BANK_ROOT[scope]}/assessment-tests/${id}`),
}
