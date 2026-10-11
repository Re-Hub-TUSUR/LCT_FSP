import type {
  CandidateFilterParams,
  CandidateFiltersDto,
  CandidateRelaxationDto,
  FspDiscipline,
  JobStatus,
} from '@/entities/candidate'
import { GRADES } from '@/entities/category'
import { EMPLOYMENT_TYPES, WORK_FORMATS } from '@/entities/vacancy'
import type { FspResult } from '@/entities/vacancy'
import { sameItems } from '@/shared/lib'
import type { MarkState } from '@/shared/ui'

export const EMPTY_FILTERS: CandidateFiltersDto = {
  specializations: [],
  grades: [],
  verifiedOnly: false,
  hasFsp: null,
  fspResult: null,
  fspDiscipline: null,
  experienceMin: null,
  stack: [],
  nice: [],
  salaryMin: null,
  salaryMax: null,
  workFormats: [],
  cities: [],
  cityIds: [],
  relocation: true,
  employmentTypes: [],
  jobStatuses: [],
  activeDays: null,
}

export const FSP_DISCIPLINES: readonly FspDiscipline[] = [
  'algorithmic',
  'product',
  'security',
  'robotics',
  'uav',
]
export const FSP_DISCIPLINE_SHORT: Record<FspDiscipline, string> = {
  algorithmic: 'Алгоритмическое',
  product: 'Продуктовое',
  security: 'Защита информации',
  robotics: 'Робототехника',
  uav: 'БАС',
}
/** «Любой» is the default: taking part is a result too. */
export const FSP_RESULT_STEPS: readonly { value: FspResult | null; label: string }[] = [
  { value: null, label: 'Любой' },
  { value: 'finalist', label: 'Финалист+' },
  { value: 'prizewinner', label: 'Призёр' },
]
export const EXPERIENCE_STEPS: readonly { value: number | null; label: string }[] = [
  { value: null, label: 'Любой' },
  { value: 1, label: '1+ год' },
  { value: 3, label: '3+ года' },
  { value: 5, label: '5+ лет' },
]
/** Not looking profiles are hidden from employers: nothing to filter by. */
export const LOOKING: readonly { value: JobStatus; label: string }[] = [
  { value: 'active', label: 'Активно ищет работу' },
  { value: 'open', label: 'Рассматривает предложения' },
]
export const ACTIVE_DAYS = 30

// Every query parameter of the filters: the URL uses the API's names.
const KEYS = [
  'specialization',
  'grade',
  'verifiedOnly',
  'hasFspAchievements',
  'fspResult',
  'fspDiscipline',
  'experienceMin',
  'stack',
  'nice',
  'salaryMin',
  'salaryMax',
  'workFormat',
  'city',
  'cityId',
  'relocation',
  'employment',
  'jobStatus',
  'activeDays',
] as const

function positive(value: string | null): number | null {
  const number = Number(value)
  return Number.isFinite(number) && number > 0 ? Math.round(number) : null
}

function oneOf<T extends string>(value: string | null, allowed: readonly T[]): T | null {
  return allowed.find((item) => item === value) ?? null
}

function listOf<T extends string>(params: URLSearchParams, key: string, allowed: readonly T[]) {
  return [...new Set(params.getAll(key))].filter((item): item is T =>
    (allowed as readonly string[]).includes(item),
  )
}

function terms(params: URLSearchParams, key: string): string[] {
  return [...new Set(params.getAll(key).map((item) => item.trim()))].filter(Boolean)
}

export function readFilters(params: URLSearchParams): CandidateFiltersDto {
  const fsp = params.get('hasFspAchievements')
  return {
    specializations: terms(params, 'specialization'),
    grades: listOf(params, 'grade', GRADES),
    verifiedOnly: params.get('verifiedOnly') === 'true',
    hasFsp: fsp === 'true' ? true : fsp === 'false' ? false : null,
    fspResult: oneOf(params.get('fspResult'), ['finalist', 'prizewinner'] as const),
    fspDiscipline: oneOf(params.get('fspDiscipline'), FSP_DISCIPLINES),
    experienceMin: positive(params.get('experienceMin')),
    stack: terms(params, 'stack'),
    nice: terms(params, 'nice'),
    salaryMin: positive(params.get('salaryMin')),
    salaryMax: positive(params.get('salaryMax')),
    workFormats: listOf(params, 'workFormat', WORK_FORMATS),
    cities: terms(params, 'city'),
    cityIds: [...new Set(params.getAll('cityId').map(Number))].filter(
      (item) => Number.isInteger(item) && item > 0,
    ),
    relocation: params.get('relocation') !== 'false',
    employmentTypes: listOf(params, 'employment', EMPLOYMENT_TYPES),
    jobStatuses: listOf(
      params,
      'jobStatus',
      LOOKING.map((item) => item.value),
    ),
    activeDays: positive(params.get('activeDays')),
  }
}

const some = <T>(values: readonly T[]) => (values.length ? [...values] : undefined)

/** The filters as the search's query parameters; defaults are left out. */
export function filterParams(filters: CandidateFiltersDto): CandidateFilterParams {
  const fsp = filters.hasFsp === true
  return {
    specialization: some(filters.specializations),
    grade: some(filters.grades),
    verifiedOnly: filters.verifiedOnly || undefined,
    hasFspAchievements: filters.hasFsp ?? undefined,
    fspResult: fsp ? (filters.fspResult ?? undefined) : undefined,
    fspDiscipline: fsp ? (filters.fspDiscipline ?? undefined) : undefined,
    experienceMin: filters.experienceMin ?? undefined,
    stack: some(filters.stack),
    nice: some(filters.nice),
    salaryMin: filters.salaryMin ?? undefined,
    salaryMax: filters.salaryMax ?? undefined,
    workFormat: some(filters.workFormats),
    city: some(filters.cities),
    cityId: some(filters.cityIds),
    relocation: filters.relocation ? undefined : false,
    employment: some(filters.employmentTypes),
    jobStatus: some(filters.jobStatuses),
    activeDays: filters.activeDays ?? undefined,
  }
}

/** `params` with the filters replaced; the page goes back to the first. */
export function writeFilters(params: URLSearchParams, filters: CandidateFiltersDto) {
  const next = new URLSearchParams(params)
  KEYS.forEach((key) => next.delete(key))
  next.delete('page')
  for (const [key, value] of Object.entries(filterParams(filters))) {
    if (Array.isArray(value)) value.forEach((item) => next.append(key, String(item)))
    else if (value !== undefined) next.set(key, String(value))
  }
  return next
}

export const onlyRemote = (filters: CandidateFiltersDto) =>
  filters.workFormats.length === 1 && filters.workFormats[0] === 'remote'

/** Groups with a value: the number next to «Фильтры». */
export function activeCount(filters: CandidateFiltersDto): number {
  return [
    filters.specializations.length,
    filters.grades.length,
    filters.verifiedOnly,
    filters.hasFsp !== null,
    filters.experienceMin,
    filters.stack.length,
    filters.nice.length,
    filters.salaryMin || filters.salaryMax,
    filters.workFormats.length,
    (filters.cityIds.length || filters.cities.length) && !onlyRemote(filters),
    !filters.relocation,
    filters.employmentTypes.length,
    filters.jobStatuses.length,
    filters.activeDays,
  ].filter(Boolean).length
}

type Key = keyof CandidateFiltersDto

function sameValue(a: CandidateFiltersDto[Key], b: CandidateFiltersDto[Key]): boolean {
  if (Array.isArray(a) && Array.isArray(b)) return sameItems(a, b)
  return (a ?? null) === (b ?? null)
}

function isDefault(key: Key, value: CandidateFiltersDto[Key]): boolean {
  return sameValue(value, EMPTY_FILTERS[key])
}

export function sameFilters(a: CandidateFiltersDto, b: CandidateFiltersDto): boolean {
  return (Object.keys(EMPTY_FILTERS) as Key[]).every((key) => sameValue(a[key], b[key]))
}

/** Panel groups a vacancy fills in, with the filters each of them shows. */
export const MARK_GROUPS = {
  specializations: ['specializations'],
  grades: ['grades', 'verifiedOnly', 'hasFsp', 'fspResult', 'fspDiscipline'],
  experience: ['experienceMin'],
  stack: ['stack', 'nice'],
  salary: ['salaryMin', 'salaryMax'],
  formats: ['workFormats'],
  location: ['cities', 'relocation'],
  employment: ['employmentTypes'],
} as const satisfies Record<string, readonly Key[]>

export type MarkGroup = keyof typeof MARK_GROUPS

/** «из вакансии» while a group is as the vacancy filled it in, «изменено» after a change. */
export function markOf(
  group: MarkGroup,
  filters: CandidateFiltersDto,
  preset: CandidateFiltersDto | null,
): MarkState {
  if (!preset) return null
  const keys: readonly Key[] = MARK_GROUPS[group]
  if (keys.every((key) => isDefault(key, preset[key]))) return null
  return keys.every((key) => sameValue(filters[key], preset[key])) ? 'source' : 'changed'
}

/** The group back as the vacancy filled it in. */
export function reverted(
  group: MarkGroup,
  filters: CandidateFiltersDto,
  preset: CandidateFiltersDto,
): CandidateFiltersDto {
  const keys: readonly Key[] = MARK_GROUPS[group]
  return Object.fromEntries(
    (Object.keys(filters) as Key[]).map((key) => [
      key,
      keys.includes(key) ? preset[key] : filters[key],
    ]),
  ) as CandidateFiltersDto
}

/** What a loosening says and the filters after it. */
export function relaxation(
  item: CandidateRelaxationDto,
  filters: CandidateFiltersDto,
): { label: string; next: CandidateFiltersDto } | null {
  const value = item.value
  switch (item.kind) {
    case 'stack':
      return value
        ? {
            label: `${value} — перенести в «Будет плюсом»`,
            next: {
              ...filters,
              stack: filters.stack.filter((term) => term !== value),
              nice: filters.nice.includes(value) ? filters.nice : [...filters.nice, value],
            },
          }
        : null
    case 'salary_max':
      return { label: 'Убрать верхнюю границу зарплаты', next: { ...filters, salaryMax: null } }
    case 'salary_min':
      return { label: 'Убрать нижнюю границу зарплаты', next: { ...filters, salaryMin: null } }
    case 'grades':
      return { label: 'Любой грейд', next: { ...filters, grades: [] } }
    case 'specializations':
      return { label: 'Любая специализация', next: { ...filters, specializations: [] } }
    case 'verified':
      return {
        label: 'Не только с подтверждённым грейдом',
        next: { ...filters, verifiedOnly: false },
      }
    case 'fsp_result':
      return { label: 'ФСП: любой результат', next: { ...filters, fspResult: null } }
    case 'fsp_discipline':
      return { label: 'ФСП: любая дисциплина', next: { ...filters, fspDiscipline: null } }
    case 'fsp':
      return {
        label: 'Без требования ФСП',
        next: { ...filters, hasFsp: null, fspResult: null, fspDiscipline: null },
      }
    case 'experience':
      return { label: 'Любой стаж', next: { ...filters, experienceMin: null } }
    case 'work_formats':
      return { label: 'Любой формат', next: { ...filters, workFormats: [] } }
    case 'relocation':
      return { label: 'Учесть готовых к переезду', next: { ...filters, relocation: true } }
    case 'cities':
      return { label: 'Любой город', next: { ...filters, cities: [], cityIds: [] } }
    case 'employment':
      return { label: 'Любая занятость', next: { ...filters, employmentTypes: [] } }
    case 'job_statuses':
      return { label: 'Любая готовность к работе', next: { ...filters, jobStatuses: [] } }
    case 'active':
      return { label: 'Любая давность активности', next: { ...filters, activeDays: null } }
  }
}
