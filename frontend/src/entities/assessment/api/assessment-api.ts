import { queryOptions } from '@tanstack/react-query'
import { http } from '@/shared/api'

export type AssessmentAttemptStatus = 'in_progress' | 'passed' | 'failed' | 'expired'

export type AssessmentAttemptDto = {
  id: string
  specialization: string
  grade: string
  status: AssessmentAttemptStatus
  score: number | null
  startedAt: string
  finishedAt: string | null
}

/** Candidate's current categorisation state and grade-change limits. */
export type AssessmentStatusDto = {
  specialization: string | null
  grade: string | null
  /** Grade can be changed not more often than the configured cooldown. */
  nextGradeChangeAt: string | null
  history: AssessmentAttemptDto[]
}

export const assessmentKeys = {
  all: ['assessments'] as const,
  status: () => [...assessmentKeys.all, 'status'] as const,
}

export const assessmentQueries = {
  status: () =>
    queryOptions({
      queryKey: assessmentKeys.status(),
      queryFn: ({ signal }) => http.get<AssessmentStatusDto>('/assessments/me', { signal }),
    }),
}
