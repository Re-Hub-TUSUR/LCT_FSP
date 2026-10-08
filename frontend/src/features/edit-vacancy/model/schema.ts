import type { FspDiscipline } from '@/entities/candidate'
import { GRADES } from '@/entities/category'
import type { Grade } from '@/entities/category'
import type {
  EmploymentType,
  FspResult,
  VacancyBenefit,
  VacancyDto,
  VacancyWrite,
  WorkFormat,
} from '@/entities/vacancy'

export type VacancyValues = {
  title: string
  specialization: string
  /** One grade or two neighbouring ones. */
  grades: Grade[]
  description: string
  stackRequired: string[]
  stackNice: string[]
  /** Rubles as typed: digits with any separators. */
  salaryFrom: string
  salaryTo: string
  workFormat: WorkFormat
  city: string
  relocationHelp: boolean
  employmentTypes: EmploymentType[]
  benefits: VacancyBenefit[]
  verifiedGradeOnly: boolean
  fspBestResult: FspResult | ''
  fspDiscipline: FspDiscipline | ''
  minExperienceYears: number
}

export type VacancyErrorKey =
  | 'title'
  | 'specialization'
  | 'grades'
  | 'description'
  | 'stackRequired'
  | 'salaryFrom'
  | 'salaryTo'
  | 'city'
  | 'employmentTypes'

export type VacancyErrors = Partial<Record<VacancyErrorKey, string>>

export const EMPTY_VACANCY: VacancyValues = {
  title: '',
  specialization: '',
  grades: [],
  description: '',
  stackRequired: [],
  stackNice: [],
  salaryFrom: '',
  salaryTo: '',
  workFormat: 'remote',
  city: '',
  relocationHelp: false,
  employmentTypes: ['full'],
  benefits: [],
  verifiedGradeOnly: true,
  fspBestResult: '',
  fspDiscipline: '',
  minExperienceYears: 0,
}

export const TITLE_MIN = 3
export const TITLE_MAX = 200
export const DESCRIPTION_MIN = 150
export const DESCRIPTION_MAX = 5000
export const STACK_MAX = 20

export const EXPERIENCE_OPTIONS = [
  { value: 0, label: 'Любой' },
  { value: 1, label: 'От года' },
  { value: 3, label: 'От 3 лет' },
  { value: 5, label: 'От 5 лет' },
] as const

/** A click on a grade: a neighbour of the only chosen one joins it, any other replaces the choice. */
export function toggleGrade(grades: Grade[], grade: Grade): Grade[] {
  if (grades.includes(grade)) return grades.filter((item) => item !== grade)
  const [only] = grades
  if (grades.length === 1 && only && Math.abs(GRADES.indexOf(only) - GRADES.indexOf(grade)) === 1) {
    return GRADES.filter((item) => item === only || item === grade)
  }
  return [grade]
}

const rubles = (text: string) => Number(text.replace(/\D/g, ''))

export function validateVacancy(values: VacancyValues): VacancyErrors {
  const errors: VacancyErrors = {}
  const title = values.title.trim()
  if (title.length < TITLE_MIN) errors.title = 'Укажите название вакансии'
  else if (title.length > TITLE_MAX) errors.title = `Не больше ${TITLE_MAX} символов`
  if (!values.specialization) errors.specialization = 'Выберите специализацию'
  if (values.grades.length === 0) errors.grades = 'Выберите грейд: один или два соседних'
  const description = values.description.trim()
  if (description.length < DESCRIPTION_MIN) {
    errors.description = `Опишите вакансию: ещё ${DESCRIPTION_MIN - description.length} символов`
  } else if (description.length > DESCRIPTION_MAX) {
    errors.description = `Не больше ${DESCRIPTION_MAX} символов`
  }
  if (values.stackRequired.length === 0) {
    errors.stackRequired = 'Добавьте хотя бы одну обязательную технологию'
  } else if (values.stackRequired.length > STACK_MAX || values.stackNice.length > STACK_MAX) {
    errors.stackRequired = `В каждом списке — не больше ${STACK_MAX} технологий`
  }
  const from = rubles(values.salaryFrom)
  const to = rubles(values.salaryTo)
  if (!from) errors.salaryFrom = 'Укажите нижнюю границу вилки'
  if (!to) errors.salaryTo = 'Укажите верхнюю границу вилки'
  else if (from && from > to) errors.salaryTo = 'Верхняя граница меньше нижней'
  if (values.workFormat !== 'remote' && !values.city.trim()) {
    errors.city = 'Укажите город для офиса или гибрида'
  }
  if (values.employmentTypes.length === 0) errors.employmentTypes = 'Выберите тип занятости'
  return errors
}

export function toVacancyPayload(values: VacancyValues, publish: boolean): VacancyWrite {
  const remote = values.workFormat === 'remote'
  const taken = new Set(values.stackRequired.map((skill) => skill.toLocaleLowerCase('ru')))
  return {
    title: values.title.trim(),
    description: values.description.trim(),
    specialization: values.specialization,
    grades: values.grades,
    stackRequired: values.stackRequired,
    stackNice: values.stackNice.filter((skill) => !taken.has(skill.toLocaleLowerCase('ru'))),
    salary: { from: rubles(values.salaryFrom), to: rubles(values.salaryTo) },
    workFormat: values.workFormat,
    city: remote ? null : values.city.trim(),
    relocationHelp: !remote && values.relocationHelp,
    employmentTypes: values.employmentTypes,
    benefits: values.benefits,
    verifiedGradeOnly: values.verifiedGradeOnly,
    fspBestResult: values.fspBestResult || null,
    // A discipline only narrows the result asked for.
    fspDiscipline: values.fspBestResult ? values.fspDiscipline || null : null,
    minExperienceYears: values.minExperienceYears,
    publish,
  }
}

export function vacancyValuesFrom(vacancy: VacancyDto | null): VacancyValues {
  if (!vacancy) return EMPTY_VACANCY
  // Older vacancies have one flat stack and one grade: treat the stack as required.
  const required = vacancy.stackRequired.length > 0 ? vacancy.stackRequired : vacancy.stack
  return {
    title: vacancy.title,
    specialization: vacancy.category.specialization,
    grades: vacancy.grades.length > 0 ? vacancy.grades : [vacancy.category.grade],
    description: vacancy.description,
    stackRequired: required,
    stackNice: vacancy.stackNice.filter((skill) => !required.includes(skill)),
    salaryFrom: String(vacancy.salary.from),
    salaryTo: String(vacancy.salary.to),
    workFormat: vacancy.workFormat,
    city: vacancy.city ?? '',
    relocationHelp: vacancy.relocationHelp,
    employmentTypes: vacancy.employmentTypes.length > 0 ? vacancy.employmentTypes : ['full'],
    benefits: vacancy.benefits,
    verifiedGradeOnly: vacancy.verifiedGradeOnly,
    fspBestResult: vacancy.fspBestResult ?? '',
    fspDiscipline: (vacancy.fspDiscipline as FspDiscipline | null) ?? '',
    minExperienceYears: vacancy.minExperienceYears ?? 0,
  }
}
