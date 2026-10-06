import type { CandidateProfileUpdate, OwnCandidateDto, ResumeCreate } from '@/entities/candidate'
import type { WorkFormat } from '@/entities/vacancy'
import { WORK_FORMATS } from '@/entities/vacancy'

export type ResumeValues = {
  displayName: string
  headline: string
  specialization: string
  city: string
  experienceYears: string
  workFormats: WorkFormat[]
  stack: string[]
  softSkills: string[]
  about: string
  phone: string
  telegram: string
  salary: string
}

export type ResumeErrors = Partial<Record<keyof ResumeValues, string>>

export const EMPTY_RESUME: ResumeValues = {
  displayName: '',
  headline: '',
  specialization: '',
  city: '',
  experienceYears: '',
  workFormats: [],
  stack: [],
  softSkills: [],
  about: '',
  phone: '',
  telegram: '',
  salary: '',
}

const FORMATS = new Set<string>(WORK_FORMATS)

export function splitList(value: string): string[] {
  const seen = new Set<string>()
  const items: string[] = []
  for (const part of value.split(/[,;\n]/)) {
    const skill = part.trim().replace(/\s+/g, ' ')
    if (!skill) continue
    const key = skill.toLocaleLowerCase('ru')
    if (seen.has(key)) continue
    seen.add(key)
    items.push(skill)
  }
  return items
}

function wholeNumber(value: string): number | null {
  if (!/^\d+$/.test(value.trim())) return null
  return Number(value.trim())
}

function listError(items: string[], limit: number): string | undefined {
  if (items.length > limit) return `Не больше ${limit} пунктов`
  const long = items.find((item) => item.length > 40)
  if (long) return `«${long.slice(0, 40)}» длиннее 40 символов`
  return undefined
}

export function validateResume(values: ResumeValues): ResumeErrors {
  const errors: ResumeErrors = {}
  if (!values.displayName.trim()) errors.displayName = 'Укажите имя и фамилию'
  if (!values.headline.trim()) errors.headline = 'Укажите должность'
  if (!values.specialization) errors.specialization = 'Выберите специализацию'
  if (!values.city.trim()) errors.city = 'Укажите город'
  const years = wholeNumber(values.experienceYears)
  if (years === null || years > 50) errors.experienceYears = 'Стаж — целое число от 0 до 50'
  if (values.workFormats.length === 0) errors.workFormats = 'Выберите формат работы'
  if (values.workFormats.some((format) => !FORMATS.has(format))) {
    errors.workFormats = 'Выберите формат из списка'
  }
  if (values.stack.length === 0) errors.stack = 'Укажите хотя бы один навык'
  else {
    const stack = listError(values.stack, 30)
    if (stack) errors.stack = stack
  }
  const soft = listError(values.softSkills, 20)
  if (soft) errors.softSkills = soft
  if (values.about.trim().length > 2000) errors.about = 'Не больше 2000 символов'
  if (values.phone.trim().length > 32) errors.phone = 'Слишком длинный номер'
  if (values.telegram.trim().length > 64) errors.telegram = 'Слишком длинный ник'
  if (values.salary.trim()) {
    const salary = wholeNumber(values.salary)
    if (salary === null || salary <= 0) errors.salary = 'Сумма — целое число больше нуля'
  }
  return errors
}

export function validateExtra(values: ResumeValues): ResumeErrors {
  const errors: ResumeErrors = {}
  if (!values.headline.trim()) errors.headline = 'Укажите должность'
  if (!values.specialization) errors.specialization = 'Выберите специализацию'
  const years = wholeNumber(values.experienceYears)
  if (years === null || years > 50) errors.experienceYears = 'Стаж — целое число от 0 до 50'
  if (values.stack.length === 0) errors.stack = 'Укажите хотя бы один навык'
  else {
    const stack = listError(values.stack, 30)
    if (stack) errors.stack = stack
  }
  const soft = listError(values.softSkills, 20)
  if (soft) errors.softSkills = soft
  if (values.about.trim().length > 2000) errors.about = 'Не больше 2000 символов'
  return errors
}

export function toExtraResume(values: ResumeValues): ResumeCreate {
  return {
    headline: values.headline.trim(),
    specialization: values.specialization,
    stack: values.stack,
    softSkills: values.softSkills,
    about: values.about.trim() || null,
    experienceYears: Number(values.experienceYears.trim()),
  }
}

export function toResumePayload(values: ResumeValues): CandidateProfileUpdate {
  const salary = values.salary.trim() ? Number(values.salary.trim()) : null
  return {
    displayName: values.displayName.trim(),
    headline: values.headline.trim(),
    specialization: values.specialization,
    city: values.city.trim(),
    experienceYears: Number(values.experienceYears.trim()),
    workFormats: values.workFormats,
    stack: values.stack,
    softSkills: values.softSkills,
    about: values.about.trim() || null,
    phone: values.phone.trim() || null,
    telegram: values.telegram.trim().replace(/^@+/, '') || null,
    salaryExpectation: salary,
  }
}

export function resumeValuesFrom(profile: OwnCandidateDto | null): ResumeValues {
  if (!profile) return EMPTY_RESUME
  return {
    displayName: profile.displayName,
    headline: profile.headline ?? '',
    specialization: profile.specialization ?? profile.category?.specialization ?? '',
    city: profile.city ?? '',
    experienceYears: profile.experienceYears == null ? '' : String(profile.experienceYears),
    workFormats: profile.workFormats,
    stack: profile.stack,
    softSkills: profile.softSkills,
    about: profile.about ?? '',
    phone: profile.contacts?.phone ?? '',
    telegram: profile.contacts?.telegram ?? '',
    salary: profile.salaryExpectation == null ? '' : String(profile.salaryExpectation),
  }
}
