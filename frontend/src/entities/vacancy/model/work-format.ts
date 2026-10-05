export const WORK_FORMATS = ['office', 'hybrid', 'remote'] as const

export type WorkFormat = (typeof WORK_FORMATS)[number]

export const WORK_FORMAT_LABELS: Record<WorkFormat, string> = {
  office: 'Офис',
  hybrid: 'Гибрид',
  remote: 'Удалённо',
}
