import type { CandidateProfileUpdate } from '@/entities/candidate'
import { toResumePayload, validateResume } from './schema'
import type { ResumeErrors, ResumeValues } from './schema'

export type PanelId =
  'basic' | 'search' | 'experience' | 'skills' | 'education' | 'about' | 'contacts'

export const PANELS: PanelId[] = [
  'basic',
  'search',
  'experience',
  'skills',
  'education',
  'about',
  'contacts',
]

export const PANEL_TITLES: Record<PanelId, string> = {
  basic: 'Основное',
  search: 'Поиск работы',
  experience: 'Опыт работы',
  skills: 'Навыки',
  education: 'Образование',
  about: 'О себе',
  contacts: 'Контакты',
}

/** Form fields of a panel, in the order the first invalid one gets the focus. */
export const PANEL_FIELDS: Record<PanelId, (keyof ResumeValues)[]> = {
  basic: ['displayName', 'headline', 'specialization', 'city', 'birthDate'],
  search: ['jobStatus', 'salary', 'relocationReady', 'workFormats', 'employmentTypes'],
  experience: ['noExperience', 'experienceYears', 'experience'],
  skills: ['stack', 'softSkills'],
  education: ['education'],
  about: ['about'],
  contacts: ['phone', 'telegram', 'githubUrl'],
}

type PayloadKey = keyof CandidateProfileUpdate

/** What PATCH /candidates/me receives for a panel: only its own columns. */
const PANEL_PAYLOAD: Record<PanelId, PayloadKey[]> = {
  basic: ['displayName', 'headline', 'specialization', 'cityId', 'birthDate'],
  search: ['jobStatus', 'salaryExpectation', 'relocationReady', 'workFormats', 'employmentTypes'],
  experience: ['noExperience', 'experienceYears', 'experienceEntries'],
  skills: ['stack', 'softSkills'],
  education: ['education'],
  about: ['about'],
  contacts: ['phone', 'telegram', 'githubUrl'],
}

export function validatePanels(values: ResumeValues, panels: PanelId[]): ResumeErrors {
  const all = validateResume(values)
  const errors: ResumeErrors = {}
  for (const panel of panels) {
    for (const field of PANEL_FIELDS[panel]) {
      if (all[field]) errors[field] = all[field]
    }
  }
  return errors
}

export function panelsPayload(
  values: ResumeValues,
  panels: PanelId[],
): Partial<CandidateProfileUpdate> {
  const full = toResumePayload(values)
  const payload: Record<string, unknown> = {}
  for (const panel of panels) {
    for (const key of PANEL_PAYLOAD[panel]) payload[key] = full[key]
  }
  return payload as Partial<CandidateProfileUpdate>
}

function same(a: unknown, b: unknown): boolean {
  return JSON.stringify(a) === JSON.stringify(b)
}

/** Panels whose fields a recognised resume changed: they open together for a check. */
export function changedPanels(before: ResumeValues, after: ResumeValues): PanelId[] {
  return PANELS.filter((panel) =>
    PANEL_FIELDS[panel].some((field) => !same(before[field], after[field])),
  )
}
