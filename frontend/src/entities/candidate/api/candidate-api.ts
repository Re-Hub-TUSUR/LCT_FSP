import { queryOptions } from '@tanstack/react-query'
import { http } from '@/shared/api'
import type { Paginated, PaginationParams } from '@/shared/api'
import type { CategoryDto, Grade, SpecializationCode } from '@/entities/category/@x/candidate'

export type FspAchievementDto = {
  eventName: string
  year: number
  place: number | null
  discipline: string
}

/** Contacts are revealed only after the candidate accepted an invitation or applied (ТЗ 2.2). */
export type CandidateContactsDto = {
  email: string
  phone: string | null
  telegram: string | null
}

export type CandidateDto = {
  id: string
  displayName: string
  headline: string | null
  category: CategoryDto | null
  stack: string[]
  experienceYears: number | null
  assessmentScore: number | null
  /** Empty list is a valid, explicitly handled state: candidate has no FSP history. */
  fspAchievements: FspAchievementDto[]
  fspLinked: boolean
  contacts: CandidateContactsDto | null
}

export type CandidateSearchParams = PaginationParams & {
  specialization?: SpecializationCode
  grade?: Grade
  stack?: string[]
  hasFspAchievements?: boolean
}

export const candidateKeys = {
  all: ['candidates'] as const,
  detail: (id: string) => [...candidateKeys.all, 'detail', id] as const,
  search: (params: CandidateSearchParams) => [...candidateKeys.all, 'search', params] as const,
}

export const candidateQueries = {
  detail: (id: string) =>
    queryOptions({
      queryKey: candidateKeys.detail(id),
      queryFn: ({ signal }) => http.get<CandidateDto>(`/candidates/${id}`, { signal }),
      enabled: Boolean(id),
    }),
  search: (params: CandidateSearchParams) =>
    queryOptions({
      queryKey: candidateKeys.search(params),
      queryFn: ({ signal }) =>
        http.get<Paginated<CandidateDto>>('/candidates', { query: params, signal }),
    }),
}
