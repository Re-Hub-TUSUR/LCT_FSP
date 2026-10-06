import { queryOptions } from '@tanstack/react-query'
import { http } from '@/shared/api'
import type { Paginated, PaginationParams, SalaryRangeDto } from '@/shared/api'
import type { CategoryDto, Grade, SpecializationCode } from '@/entities/category/@x/vacancy'
import type { WorkFormat } from '../model/work-format'

export type CompanyBriefDto = {
  id: string
  name: string
  industry: string | null
  city: string | null
  size: string | null
}

export type VacancyDto = {
  id: string
  title: string
  company: CompanyBriefDto
  category: CategoryDto
  stack: string[]
  salary: SalaryRangeDto
  workFormat: WorkFormat
  /** Office location; null for remote positions. */
  city: string | null
  description: string
  /** Null for a draft, visible only to its company. */
  publishedAt: string | null
}

export type Reaction = 'like' | 'skip'

/** Which cards a feed returns: all except hidden, not decided yet (swipes) or favourites. */
export type FeedView = 'all' | 'unseen' | 'liked'

/** One card of the candidate's feed with the explanation of its position. */
export type VacancyMatchDto = {
  vacancy: VacancyDto
  /** 0..1; null when the feed is not personalised yet. */
  matchScore: number | null
  reasons: string[]
  reaction: Reaction | null
}

export type FeedBasisDto = {
  category: CategoryDto | null
  gradeVerified: boolean
  stack: string[]
  workFormats: WorkFormat[]
  city: string | null
  salaryExpectation: number | null
}

export type VacancyFeedDto = Paginated<VacancyMatchDto> & {
  personalized: boolean
  basis: FeedBasisDto | null
}

export type VacancyFeedParams = PaginationParams & {
  view?: FeedView
  workFormat?: WorkFormat[]
  salaryMin?: number
}

export type VacancyListParams = PaginationParams & {
  search?: string
  specialization?: SpecializationCode
  grade?: Grade
  workFormat?: WorkFormat
}

export const vacancyKeys = {
  all: ['vacancies'] as const,
  list: (params: VacancyListParams) => [...vacancyKeys.all, 'list', params] as const,
  feed: (params: VacancyFeedParams) => [...vacancyKeys.all, 'feed', params] as const,
  mine: () => [...vacancyKeys.all, 'mine'] as const,
  detail: (id: string) => [...vacancyKeys.all, 'detail', id] as const,
}

export const vacancyQueries = {
  list: (params: VacancyListParams = {}) =>
    queryOptions({
      queryKey: vacancyKeys.list(params),
      queryFn: ({ signal }) =>
        http.get<Paginated<VacancyDto>>('/vacancies', { query: params, signal }),
    }),
  /** Candidate's personal feed: relevant vacancies only, ranked by fit. */
  feed: (params: VacancyFeedParams) =>
    queryOptions({
      queryKey: vacancyKeys.feed(params),
      queryFn: ({ signal }) =>
        http.get<VacancyFeedDto>('/vacancies/feed', { query: params, signal }),
    }),
  /** Employer's own vacancies (drafts included): the context for hiring by fit. */
  mine: () =>
    queryOptions({
      queryKey: vacancyKeys.mine(),
      queryFn: ({ signal }) =>
        http.get<Paginated<VacancyDto>>('/vacancies/mine', { query: { perPage: 100 }, signal }),
    }),
  detail: (id: string) =>
    queryOptions({
      queryKey: vacancyKeys.detail(id),
      queryFn: ({ signal }) => http.get<VacancyDto>(`/vacancies/${id}`, { signal }),
      enabled: Boolean(id),
    }),
}

export const vacancyApi = {
  react: (id: string, kind: Reaction) => http.put<unknown>(`/vacancies/${id}/reaction`, { kind }),
  clearReaction: (id: string) => http.delete<void>(`/vacancies/${id}/reaction`),
}
