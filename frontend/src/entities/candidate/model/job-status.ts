export const JOB_STATUSES = ['active', 'open', 'not_looking'] as const

export type JobStatus = (typeof JOB_STATUSES)[number]

export const JOB_STATUS_LABELS: Record<JobStatus, string> = {
  active: 'Активно ищу работу',
  open: 'Открыт к предложениям',
  not_looking: 'Не ищу работу',
}

/** `not_looking` hides the profile from the employers' search. */
export const JOB_STATUS_HINTS: Record<JobStatus, string> = {
  active: 'Профиль виден работодателям и поднимается выше в подборке.',
  open: 'Профиль виден работодателям.',
  not_looking: 'Профиль скрыт из поиска, приглашения не приходят.',
}

export type FspSync = 'yes' | 'later' | 'never'

export const FSP_SYNC_LABELS: Record<FspSync, string> = {
  yes: 'Да',
  later: 'Позже',
  never: 'Не участвовал',
}
