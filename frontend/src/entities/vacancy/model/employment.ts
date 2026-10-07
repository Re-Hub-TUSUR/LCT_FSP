export const EMPLOYMENT_TYPES = ['full', 'part', 'project', 'internship'] as const

export type EmploymentType = (typeof EMPLOYMENT_TYPES)[number]

export const EMPLOYMENT_LABELS: Record<EmploymentType, string> = {
  full: 'Полная',
  part: 'Частичная',
  project: 'Проектная',
  internship: 'Стажировка',
}

export type VacancyBenefit = 'dms' | 'flexible_start' | 'labor_code'

export const BENEFIT_LABELS: Record<VacancyBenefit, string> = {
  dms: 'ДМС',
  flexible_start: 'Гибкое начало дня',
  labor_code: 'Оформление по ТК РФ',
}

export type FspResult = 'participant' | 'finalist' | 'prizewinner'

export const FSP_RESULT_LABELS: Record<FspResult, string> = {
  participant: 'Участник',
  finalist: 'Финалист',
  prizewinner: 'Призёр',
}

/** Salaries on the platform are net, per month. */
export const SALARY_NOTE = 'на руки, в месяц'
