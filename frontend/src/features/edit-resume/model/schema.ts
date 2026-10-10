import type {
  CandidateProfileUpdate,
  FspSync,
  JobStatus,
  OwnCandidateDto,
  ResumeCreate,
  ResumeDraftDto,
} from '@/entities/candidate'
import type { EmploymentType, WorkFormat } from '@/entities/vacancy'
import { WORK_FORMATS } from '@/entities/vacancy'
import { MAX_SALARY, MAX_SALARY_ERROR } from '@/shared/config'

/** Form row of a place of work; `stack` is typed as a comma list. */
export type ExperienceRow = {
  company: string
  position: string
  start: string
  end: string
  stack: string
}

export type EducationRow = { institution: string; specialty: string; year: string }

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
  birthDate: string
  relocationReady: boolean
  jobStatus: JobStatus
  employmentTypes: EmploymentType[]
  noExperience: boolean
  experience: ExperienceRow[]
  education: EducationRow[]
  githubUrl: string
}

export type ResumeErrors = Partial<Record<keyof ResumeValues, string>>

/** In the order of the form: the first invalid field gets the focus. */
export const RESUME_FIELD_IDS: Record<keyof ResumeValues, string> = {
  displayName: 'resume-name',
  headline: 'resume-headline',
  specialization: 'resume-specialization',
  city: 'resume-city',
  birthDate: 'resume-birth',
  jobStatus: 'resume-status',
  salary: 'resume-salary',
  relocationReady: 'resume-relocation',
  workFormats: 'resume-format-office',
  employmentTypes: 'resume-employment-full',
  noExperience: 'resume-no-experience',
  experienceYears: 'resume-experience',
  experience: 'experience-0-company',
  stack: 'resume-stack',
  softSkills: 'resume-soft',
  education: 'education-0-institution',
  about: 'resume-about',
  phone: 'resume-phone',
  telegram: 'resume-telegram',
  githubUrl: 'resume-github',
}

export const EMPTY_EXPERIENCE: ExperienceRow = {
  company: '',
  position: '',
  start: '',
  end: '',
  stack: '',
}

export const EMPTY_EDUCATION: EducationRow = { institution: '', specialty: '', year: '' }

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
  birthDate: '',
  relocationReady: false,
  jobStatus: 'open',
  employmentTypes: [],
  noExperience: false,
  experience: [],
  education: [],
  githubUrl: '',
}

/** Answers from the start screen, sent with the first save. */
export type ResumeConsents = { profileDisplayConsent: boolean; fspSync: FspSync | null }

export const MIN_STACK = 3
export const MIN_AGE = 14
const ADULT_AGE = 18
const MONTH = /^\d{4}-(0[1-9]|1[0-2])$/
const GITHUB = /^(https?:\/\/)?(www\.)?github\.com\/[\w.-]+\/?$/i

const FORMATS = new Set<string>(WORK_FORMATS)

export function ageOn(birthDate: string, today: Date = new Date()): number | null {
  const born = new Date(`${birthDate}T00:00:00`)
  if (Number.isNaN(born.getTime())) return null
  let age = today.getFullYear() - born.getFullYear()
  const beforeBirthday =
    today.getMonth() < born.getMonth() ||
    (today.getMonth() === born.getMonth() && today.getDate() < born.getDate())
  if (beforeBirthday) age -= 1
  return age
}

export function isMinor(birthDate: string, today?: Date): boolean {
  const age = ageOn(birthDate, today)
  return age !== null && age < ADULT_AGE
}

function monthIndex(value: string): number {
  const [year, month] = value.split('-').map(Number)
  return (year ?? 0) * 12 + (month ?? 1) - 1
}

/** Whole years of work; overlapping periods count once, an open period runs to today. */
export function experienceYearsOf(rows: ExperienceRow[], today: Date = new Date()): number {
  const now = today.getFullYear() * 12 + today.getMonth()
  const spans = rows
    .filter((row) => MONTH.test(row.start))
    .map((row) => [monthIndex(row.start), MONTH.test(row.end) ? monthIndex(row.end) : now] as const)
    .filter(([start, end]) => end >= start)
    // oxlint-disable-next-line unicorn/no-array-sort -- a copy is sorted; toSorted() needs ES2023
    .sort((a, b) => a[0] - b[0])
  let months = 0
  let cursor = -Infinity
  for (const [start, end] of spans) {
    const from = Math.max(start, cursor)
    if (end + 1 > from) months += end + 1 - from
    cursor = Math.max(cursor, end + 1)
  }
  return Math.floor(months / 12)
}

function experienceError(rows: ExperienceRow[], today: Date = new Date()): string | undefined {
  const now = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}`
  for (const [index, row] of rows.entries()) {
    const place = `Место работы ${index + 1}`
    if (!row.company.trim() || !row.position.trim()) return `${place}: укажите компанию и должность`
    if (!MONTH.test(row.start)) return `${place}: укажите месяц начала`
    if (row.start > now) return `${place}: начало в будущем`
    if (row.end && !MONTH.test(row.end)) return `${place}: проверьте месяц окончания`
    if (row.end && row.end < row.start) return `${place}: окончание раньше начала`
  }
  return undefined
}

function educationError(rows: EducationRow[]): string | undefined {
  for (const [index, row] of rows.entries()) {
    if (!row.institution.trim()) return `Образование ${index + 1}: укажите учебное заведение`
    if (row.year.trim()) {
      const year = Number(row.year.trim())
      if (!Number.isInteger(year) || year < 1950 || year > 2100) {
        return `Образование ${index + 1}: год — четыре цифры`
      }
    }
  }
  return undefined
}

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
  if (values.birthDate) {
    const age = ageOn(values.birthDate)
    if (age === null || age < 0) errors.birthDate = 'Проверьте дату рождения'
    else if (age < MIN_AGE) errors.birthDate = `Регистрация доступна с ${MIN_AGE} лет`
  }
  if (!values.noExperience) {
    if (values.experience.length > 0) {
      const experience = experienceError(values.experience)
      if (experience) errors.experience = experience
    } else {
      const years = wholeNumber(values.experienceYears)
      if (values.experienceYears.trim() === '') {
        errors.experienceYears = 'Укажите стаж, добавьте место работы или отметьте «Нет опыта»'
      } else if (years === null || years > 50) {
        errors.experienceYears = 'Стаж — целое число от 0 до 50'
      }
    }
  }
  if (values.workFormats.length === 0) errors.workFormats = 'Выберите формат работы'
  if (values.workFormats.some((format) => !FORMATS.has(format))) {
    errors.workFormats = 'Выберите формат из списка'
  }
  if (values.employmentTypes.length === 0) errors.employmentTypes = 'Выберите тип занятости'
  if (values.stack.length < MIN_STACK) {
    errors.stack = `Укажите не меньше ${MIN_STACK} технологий`
  } else {
    const stack = listError(values.stack, 30)
    if (stack) errors.stack = stack
  }
  const soft = listError(values.softSkills, 20)
  if (soft) errors.softSkills = soft
  const education = educationError(values.education)
  if (education) errors.education = education
  if (values.githubUrl.trim() && !GITHUB.test(values.githubUrl.trim())) {
    errors.githubUrl = 'Ссылка на профиль: github.com/логин'
  }
  if (values.about.trim().length > 2000) errors.about = 'Не больше 2000 символов'
  if (values.phone.trim().length > 32) errors.phone = 'Слишком длинный номер'
  if (values.telegram.trim().length > 64) errors.telegram = 'Слишком длинный ник'
  if (!values.phone.trim() && !values.telegram.trim().replace(/^@+/, '')) {
    errors.phone = 'Укажите телефон или Telegram'
  }
  if (values.salary.trim()) {
    const salary = wholeNumber(values.salary)
    if (salary === null || salary <= 0) errors.salary = 'Сумма — целое число больше нуля'
    else if (salary > MAX_SALARY) errors.salary = MAX_SALARY_ERROR
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

export function toResumePayload(
  values: ResumeValues,
  consents?: ResumeConsents,
): CandidateProfileUpdate {
  const salary = values.salary.trim() ? Number(values.salary.trim()) : null
  const experience = values.noExperience ? [] : values.experience
  const years = values.noExperience
    ? 0
    : experience.length > 0
      ? experienceYearsOf(experience)
      : Number(values.experienceYears.trim())
  return {
    displayName: values.displayName.trim(),
    headline: values.headline.trim(),
    specialization: values.specialization,
    city: values.city.trim(),
    experienceYears: years,
    workFormats: values.workFormats,
    stack: values.stack,
    softSkills: values.softSkills,
    about: values.about.trim() || null,
    phone: values.phone.trim() || null,
    telegram: values.telegram.trim().replace(/^@+/, '') || null,
    salaryExpectation: salary,
    birthDate: values.birthDate || null,
    relocationReady: values.relocationReady,
    jobStatus: values.jobStatus,
    employmentTypes: values.employmentTypes,
    noExperience: values.noExperience,
    experienceEntries: experience.map((row) => ({
      company: row.company.trim(),
      position: row.position.trim(),
      start: row.start,
      end: row.end || null,
      stack: splitList(row.stack),
    })),
    education: values.education.map((row) => ({
      institution: row.institution.trim(),
      specialty: row.specialty.trim() || null,
      year: row.year.trim() ? Number(row.year.trim()) : null,
    })),
    githubUrl: values.githubUrl.trim() || null,
    ...consents,
  }
}

function draftText(value: string | null, current: string): string {
  return value?.trim() || current
}

function draftList<T>(value: T[], current: T[]): T[] {
  return value.length > 0 ? value : current
}

function draftNumber(value: number | null, current: string): string {
  return value == null ? current : String(value)
}

/** Fills the form from a recognised resume; what the file does not say keeps its current value. */
export function applyResumeDraft(values: ResumeValues, draft: ResumeDraftDto): ResumeValues {
  return {
    ...values,
    displayName: draftText(draft.displayName, values.displayName),
    headline: draftText(draft.headline, values.headline),
    specialization: draftText(draft.specialization, values.specialization),
    city: draftText(draft.city, values.city),
    experienceYears: draftNumber(draft.experienceYears, values.experienceYears),
    workFormats: draftList(draft.workFormats, values.workFormats),
    stack: draftList(draft.stack, values.stack),
    softSkills: draftList(draft.softSkills, values.softSkills),
    about: draftText(draft.about, values.about),
    phone: draftText(draft.phone, values.phone),
    telegram: draftText(draft.telegram, values.telegram),
    salary: draftNumber(draft.salaryExpectation, values.salary),
  }
}

export function resumeValuesFrom(profile: OwnCandidateDto | null, fallbackName = ''): ResumeValues {
  if (!profile) {
    return fallbackName ? { ...EMPTY_RESUME, displayName: fallbackName } : EMPTY_RESUME
  }
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
    birthDate: profile.birthDate ?? '',
    relocationReady: profile.relocationReady,
    jobStatus: profile.jobStatus,
    employmentTypes: profile.employmentTypes,
    noExperience: profile.noExperience,
    experience: profile.experienceEntries.map((entry) => ({
      company: entry.company,
      position: entry.position,
      start: entry.start,
      end: entry.end ?? '',
      stack: entry.stack.join(', '),
    })),
    education: profile.education.map((entry) => ({
      institution: entry.institution,
      specialty: entry.specialty ?? '',
      year: entry.year == null ? '' : String(entry.year),
    })),
    githubUrl: profile.githubUrl ?? '',
  }
}
