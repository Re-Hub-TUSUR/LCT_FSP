import { queryOptions } from '@tanstack/react-query'
import { http } from '@/shared/api'
import type { Paginated, PaginationParams } from '@/shared/api'

/** What an employer sees about the platform grade test. */
export type AssessmentStatus = 'not_taken' | 'passed' | 'failed'

/** `awaiting_review`: finished, but open answers wait for the company's grades. */
export type AssessmentAttemptStatus =
  'in_progress' | 'passed' | 'failed' | 'expired' | 'awaiting_review'

/** Every kind has a view in the runner and an editor in the bank, see the kind registries. */
export type TaskKind = 'quiz' | 'code' | 'open'
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
  /** Set for a test a company sent; null for a platform grade test. */
  assignmentId: string | null
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

export type QuizAnswerDto = { selected: number[] }
export type OpenAnswerDto = { text: string }

type AttemptTaskBase = {
  id: string
  topic: string
  difficulty: TaskDifficulty
  title: string
  statement: string
}

/** Options come in the order shown to this candidate; the answer holds positions in it. */
export type QuizTaskDto = AttemptTaskBase & {
  kind: 'quiz'
  content: { options: string[]; multiple: boolean }
  answer: QuizAnswerDto | null
}

export type CodeTaskDto = AttemptTaskBase & {
  kind: 'code'
  content: {
    languages: { id: string; label: string }[]
    timeLimit: number
    samples: { input: string; expected: string }[]
  }
  answer: CodeAnswerDto | null
}

export type OpenTaskDto = AttemptTaskBase & {
  kind: 'open'
  content: { maxLength: number }
  answer: OpenAnswerDto | null
}

/** Candidate view of a task: never carries correct options, hidden tests or grading notes. */
export type AttemptTaskDto = QuizTaskDto | CodeTaskDto | OpenTaskDto

export type TaskAnswerDto = NonNullable<AttemptTaskDto['answer']>

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

/** One specialization the candidate has tried: its own category and its own cooldown. */
export type AssessmentTrackDto = {
  specialization: string
  /** `passed`: the grade is confirmed; `failed`: tried, nothing confirmed yet. */
  status: Exclude<AssessmentStatus, 'not_taken'>
  grade: string | null
  score: number | null
  /** Null = a test of this specialization may start right now. */
  nextAttemptAt: string | null
  /** The category employers see in search and feeds. */
  isPrimary: boolean
}

/** What a platform grade test consists of, shown before the candidate starts it. */
export type AssessmentTemplateDto = {
  grade: string
  /** Null = applies to every specialization without its own template. */
  specialization: string | null
  durationMinutes: number
  passScore: number
  tasks: Partial<Record<TaskKind, number>>
  retryDays: number
  gradeChangeDays: number
}

/** Candidate's categorisation state and what they may do next. */
export type AssessmentStatusDto = {
  /** The primary category; the fields are null until one is confirmed. */
  status: AssessmentStatus
  specialization: string | null
  grade: string | null
  score: number | null
  nextAttemptAt: string | null
  /** Every specialization the candidate has tried, confirmed ones first. */
  tracks: AssessmentTrackDto[]
  activeAttemptId: string | null
  /** False until the code runner key is configured on the server. */
  codeRunnerAvailable: boolean
  history: AssessmentAttemptDto[]
}

export type AnswerPayload = { taskId: string; answer: TaskAnswerDto }

export const assessmentKeys = {
  all: ['assessments'] as const,
  status: () => [...assessmentKeys.all, 'status'] as const,
  templates: () => [...assessmentKeys.all, 'templates'] as const,
  attempt: (id: string) => [...assessmentKeys.all, 'attempt', id] as const,
}

export const assessmentQueries = {
  status: () =>
    queryOptions({
      queryKey: assessmentKeys.status(),
      queryFn: ({ signal }) => http.get<AssessmentStatusDto>('/assessments/me', { signal }),
    }),
  templates: () =>
    queryOptions({
      queryKey: assessmentKeys.templates(),
      queryFn: ({ signal }) =>
        http.get<AssessmentTemplateDto[]>('/assessments/templates', { signal }),
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
  setPrimary: (specialization: string) =>
    http.put<AssessmentStatusDto>('/assessments/me/primary', { specialization }),
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

export type OpenPayloadDto = {
  maxLength: number
  /** What a good answer covers: reviewers only, the candidate never sees it. */
  guidance: string | null
}

export type TaskPayloadDto = QuizPayloadDto | CodePayloadDto | OpenPayloadDto

type BankTaskBase = {
  difficulty: TaskDifficulty
  specializations: string[]
  topic: string
  title: string
  statement: string
  isActive: boolean
}

/** A task as authors write it; also one item of a bank export or import file. */
export type BankTaskWrite = BankTaskBase &
  (
    | { kind: 'quiz'; payload: QuizPayloadDto }
    | { kind: 'code'; payload: CodePayloadDto }
    | { kind: 'open'; payload: OpenPayloadDto }
  )

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
  /** Platform templates: null = the test of the grade for every specialization. */
  specialization: string | null
  durationMinutes: number
  passScore: number
  quizWeight: number
  composition: CompositionDto
  /** Null = the platform defaults. */
  retryDays: number | null
  gradeChangeDays: number | null
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

export type BankTaskParams = PaginationParams & {
  kind?: TaskKind
  /** Title or topic. */
  q?: string
}

export const bankKeys = {
  all: (scope: BankScope) => ['assessment-bank', scope] as const,
  tasks: (scope: BankScope) => [...bankKeys.all(scope), 'tasks'] as const,
  taskPage: (scope: BankScope, params: BankTaskParams) =>
    [...bankKeys.tasks(scope), params] as const,
  tests: (scope: BankScope) => [...bankKeys.all(scope), 'tests'] as const,
}

export const bankQueries = {
  /** One page of the bank for the table. */
  tasks: (scope: BankScope, params: BankTaskParams = {}) =>
    queryOptions({
      queryKey: bankKeys.taskPage(scope, params),
      queryFn: ({ signal }) =>
        http.get<Paginated<BankTaskDto>>(`${BANK_ROOT[scope]}/assessment-tasks`, {
          signal,
          query: params,
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
  /** The whole bank in the import format. */
  exportTasks: (scope: BankScope) =>
    http.get<BankTaskWrite[]>(`${BANK_ROOT[scope]}/assessment-tasks/export`),
  /** All tasks or none: the first bad one cancels the file. */
  importTasks: (scope: BankScope, tasks: unknown[]) =>
    http.post<{ created: number }>(`${BANK_ROOT[scope]}/assessment-tasks/import`, tasks),
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

// ── Tests a company sends to a candidate after a match («тестовые») ─────────────────────────

export type AssignmentStatus = 'sent' | 'in_progress' | 'review' | 'done' | 'declined' | 'expired'

type NamedRef = { id: string; name: string }

export type AssignmentDto = {
  id: string
  title: string
  status: AssignmentStatus
  company: NamedRef
  candidate: NamedRef
  vacancy: NamedRef | null
  message: string | null
  durationMinutes: number
  tasksCount: number
  createdAt: string
  /** The candidate may start until then. */
  dueAt: string
  attemptId: string | null
  finishedAt: string | null
  /** Null until every answer is graded. */
  score: number | null
  passScore: number | null
}

type ReviewTaskBase = {
  id: string
  title: string
  statement: string
  answered: boolean
  /** Share of the task earned, 0..1; null = waits for the reviewer. */
  points: number | null
  /** True: graded by the reviewer, not by the platform. */
  manual: boolean
  comment: string | null
}

/** The answer next to what was expected. */
export type ReviewTaskDto = ReviewTaskBase &
  (
    | { kind: 'quiz'; review: { options: string[]; correct: number[]; selected: number[] } }
    | { kind: 'code'; review: { language: string | null; code: string | null } }
    | { kind: 'open'; review: { text: string; guidance: string | null } }
  )

export type AssignmentDetailDto = AssignmentDto & {
  /** Empty until the candidate finished. */
  tasks: ReviewTaskDto[]
  pasteCount: number
  blurCount: number
}

export type AssignmentCreatePayload = {
  testId: string
  candidateId: string
  vacancyId?: string | null
  message?: string | null
  dueAt?: string | null
}

export type ReviewGrade = { taskId: string; points: number; comment?: string | null }

export const assignmentKeys = {
  all: ['test-assignments'] as const,
  incoming: () => [...assignmentKeys.all, 'incoming'] as const,
  outgoing: () => [...assignmentKeys.all, 'outgoing'] as const,
  detail: (id: string) => [...assignmentKeys.all, 'detail', id] as const,
}

const SENT_ROOT = '/companies/me/test-assignments'

export const assignmentQueries = {
  /** Candidate: tests companies sent to me. */
  incoming: () =>
    queryOptions({
      queryKey: assignmentKeys.incoming(),
      queryFn: ({ signal }) => http.get<AssignmentDto[]>('/assessments/assignments', { signal }),
    }),
  /** Employer: tests the company sent. */
  outgoing: () =>
    queryOptions({
      queryKey: assignmentKeys.outgoing(),
      queryFn: ({ signal }) => http.get<AssignmentDto[]>(SENT_ROOT, { signal }),
    }),
  detail: (id: string) =>
    queryOptions({
      queryKey: assignmentKeys.detail(id),
      queryFn: ({ signal }) => http.get<AssignmentDetailDto>(`${SENT_ROOT}/${id}`, { signal }),
    }),
}

export const assignmentApi = {
  send: (payload: AssignmentCreatePayload) => http.post<AssignmentDto>(SENT_ROOT, payload),
  revoke: (id: string) => http.delete<void>(`${SENT_ROOT}/${id}`),
  review: (id: string, grades: ReviewGrade[]) =>
    http.put<AssignmentDetailDto>(`${SENT_ROOT}/${id}/review`, { grades }),
  start: (id: string) =>
    http.post<AttemptDetailDto>(`/assessments/assignments/${id}/start`).then(withClockOffset),
  decline: (id: string) => http.post<AssignmentDto>(`/assessments/assignments/${id}/decline`),
}
