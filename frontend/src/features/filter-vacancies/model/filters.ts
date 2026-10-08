import { BENEFIT_LABELS, BENEFITS, EMPLOYMENT_TYPES, WORK_FORMATS } from '@/entities/vacancy'
import type {
  FeedMode,
  VacancyFeedFilterParams,
  VacancyFiltersDto,
  VacancyRelaxationDto,
} from '@/entities/vacancy'
import { formatNumber, sameItems } from '@/shared/lib'
import type { MarkState } from '@/shared/ui'

export const EMPTY_FILTERS: VacancyFiltersDto = {
  salaryMin: null,
  workFormats: [],
  cities: [],
  relocation: false,
  employmentTypes: [],
  stack: [],
  nice: [],
  benefits: [],
  accredited: false,
}

// Every query parameter of the filters: the URL uses the API's names.
const KEYS = [
  'salaryMin',
  'workFormat',
  'city',
  'relocation',
  'employment',
  'stack',
  'nice',
  'benefit',
  'accredited',
] as const

function positive(value: string | null): number | null {
  const number = Number(value)
  return Number.isFinite(number) && number > 0 ? Math.round(number) : null
}

function listOf<T extends string>(params: URLSearchParams, key: string, allowed: readonly T[]) {
  return [...new Set(params.getAll(key))].filter((item): item is T =>
    (allowed as readonly string[]).includes(item),
  )
}

function terms(params: URLSearchParams, key: string): string[] {
  return [...new Set(params.getAll(key).map((item) => item.trim()))].filter(Boolean)
}

export function readFilters(params: URLSearchParams): VacancyFiltersDto {
  return {
    salaryMin: positive(params.get('salaryMin')),
    workFormats: listOf(params, 'workFormat', WORK_FORMATS),
    cities: terms(params, 'city'),
    relocation: params.get('relocation') === 'true',
    employmentTypes: listOf(params, 'employment', EMPLOYMENT_TYPES),
    stack: terms(params, 'stack'),
    nice: terms(params, 'nice'),
    benefits: listOf(params, 'benefit', BENEFITS),
    accredited: params.get('accredited') === 'true',
  }
}

const some = <T>(values: readonly T[]) => (values.length ? [...values] : undefined)

/** The filters as the feed's query parameters; defaults are left out. */
export function filterParams(filters: VacancyFiltersDto): VacancyFeedFilterParams {
  return {
    salaryMin: filters.salaryMin ?? undefined,
    workFormat: some(filters.workFormats),
    city: some(filters.cities),
    relocation: filters.relocation || undefined,
    employment: some(filters.employmentTypes),
    stack: some(filters.stack),
    nice: some(filters.nice),
    benefit: some(filters.benefits),
    accredited: filters.accredited || undefined,
  }
}

/** `params` with the filters (and the mode, when given) replaced; back to the first page. */
export function writeFilters(params: URLSearchParams, filters: VacancyFiltersDto, mode?: FeedMode) {
  const next = new URLSearchParams(params)
  KEYS.forEach((key) => next.delete(key))
  next.delete('page')
  for (const [key, value] of Object.entries(filterParams(filters))) {
    if (Array.isArray(value)) value.forEach((item) => next.append(key, String(item)))
    else if (value !== undefined) next.set(key, String(value))
  }
  if (mode) next.set('mode', mode)
  return next
}

/** Only remote work: the city does not matter. */
export const onlyRemote = (filters: VacancyFiltersDto) =>
  filters.workFormats.length > 0 && filters.workFormats.every((format) => format === 'remote')

/** Chosen filters: the number next to «Фильтры»; every condition counts. */
export function activeCount(filters: VacancyFiltersDto): number {
  return (
    [
      filters.salaryMin,
      filters.workFormats.length,
      filters.employmentTypes.length,
      filters.cities.length && !onlyRemote(filters),
      filters.relocation,
      filters.stack.length,
      filters.nice.length,
      filters.accredited,
    ].filter(Boolean).length + filters.benefits.length
  )
}

type Key = keyof VacancyFiltersDto

function sameValue(a: VacancyFiltersDto[Key], b: VacancyFiltersDto[Key]): boolean {
  if (Array.isArray(a) && Array.isArray(b)) return sameItems(a, b)
  return (a ?? null) === (b ?? null)
}

export function sameFilters(a: VacancyFiltersDto, b: VacancyFiltersDto): boolean {
  return (Object.keys(EMPTY_FILTERS) as Key[]).every((key) => sameValue(a[key], b[key]))
}

/** Panel groups the profile fills in, with the filters each of them shows. */
export const MARK_GROUPS = {
  salary: ['salaryMin'],
  formats: ['workFormats'],
  location: ['cities', 'relocation'],
  employment: ['employmentTypes'],
  stack: ['stack', 'nice'],
} as const satisfies Record<string, readonly Key[]>

export type MarkGroup = keyof typeof MARK_GROUPS

/** «из профиля» while a group is as the profile filled it in, «изменено» after a change. */
export function markOf(
  group: MarkGroup,
  filters: VacancyFiltersDto,
  preset: VacancyFiltersDto | null,
): MarkState {
  if (!preset) return null
  const keys: readonly Key[] = MARK_GROUPS[group]
  if (keys.every((key) => sameValue(preset[key], EMPTY_FILTERS[key]))) return null
  return keys.every((key) => sameValue(filters[key], preset[key])) ? 'source' : 'changed'
}

export function reverted(
  group: MarkGroup,
  filters: VacancyFiltersDto,
  preset: VacancyFiltersDto,
): VacancyFiltersDto {
  const keys: readonly Key[] = MARK_GROUPS[group]
  return Object.fromEntries(
    (Object.keys(filters) as Key[]).map((key) => [
      key,
      keys.includes(key) ? preset[key] : filters[key],
    ]),
  ) as VacancyFiltersDto
}

/** What a loosening says, the filters after it and, for `mode`, the free search. */
export function relaxation(
  item: VacancyRelaxationDto,
  filters: VacancyFiltersDto,
): { label: string; next: VacancyFiltersDto; mode?: FeedMode } | null {
  const value = item.value
  switch (item.kind) {
    case 'salary': {
      const lowered = Number(value) || 0
      return {
        label: `Снизить зарплату до ${formatNumber(lowered)} ₽`,
        next: { ...filters, salaryMin: lowered || null },
      }
    }
    case 'work_formats':
      return { label: 'Любой формат', next: { ...filters, workFormats: [] } }
    case 'employment':
      return { label: 'Любая занятость', next: { ...filters, employmentTypes: [] } }
    case 'cities':
      return { label: 'Любой город', next: { ...filters, cities: [] } }
    case 'stack':
      return value
        ? {
            label: `Перенести ${value} в «Будет плюсом»`,
            next: {
              ...filters,
              stack: filters.stack.filter((term) => term !== value),
              nice: filters.nice.includes(value) ? filters.nice : [...filters.nice, value],
            },
          }
        : null
    case 'benefit': {
      const benefit = BENEFITS.find((known) => known === value)
      return benefit
        ? {
            label: `Убрать «${BENEFIT_LABELS[benefit]}»`,
            next: { ...filters, benefits: filters.benefits.filter((chosen) => chosen !== benefit) },
          }
        : null
    }
    case 'accredited':
      return {
        label: 'Убрать «Аккредитованная IT-компания»',
        next: { ...filters, accredited: false },
      }
    case 'mode':
      return { label: 'Перейти в свободный поиск', next: filters, mode: 'free' }
  }
}
