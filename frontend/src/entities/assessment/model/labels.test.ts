import { describe, expect, it } from 'vitest'
import type { AssessmentAttemptDto } from '../api/assessment-api'
import { attemptResultLabel } from './labels'

const attempt = (patch: Partial<AssessmentAttemptDto>): AssessmentAttemptDto => ({
  id: 'a',
  assignmentId: null,
  title: 'Разработка игр · Стажёр',
  specialization: 'gamedev',
  grade: 'intern',
  status: 'failed',
  score: 100,
  passScore: 60,
  startedAt: '2026-10-10T10:00:00Z',
  expiresAt: '2026-10-10T11:00:00Z',
  finishedAt: '2026-10-10T10:30:00Z',
  breakdown: null,
  ...patch,
})

describe('attempt result', () => {
  it('says why 100 points did not pass', () => {
    expect(attemptResultLabel(attempt({ failedBy: 'interview' }))).toBe(
      'Тест пройден, ИИ-собеседование — нет',
    )
    expect(attemptResultLabel(attempt({ failedBy: 'quiz' }))).toMatch(/мало верных/)
  })

  it('keeps the plain status otherwise', () => {
    expect(attemptResultLabel(attempt({ failedBy: 'score', score: 20 }))).toBe('Не пройден')
    expect(attemptResultLabel(attempt({ status: 'passed', failedBy: null }))).toBe('Пройден')
  })
})
