import { queryOptions } from '@tanstack/react-query'
import { http } from '@/shared/api'
import type { Paginated, PaginationParams, SalaryRangeDto } from '@/shared/api'
import type { CategoryDto, Grade, SpecializationCode } from '@/entities/category/@x/vacancy'
import type { EmploymentType, FspResult, VacancyBenefit } from '../model/employment'
import type { WorkFormat } from '../model/work-format'

export type CompanyBriefDto = {
  id: string
  name: string
  industry: string | null
  city: string | null
  size: string | null
  /** An admin approved the Минцифры registry extract: the check mark next to the name. */
  itAccredited: boolean
  hasLogo: boolean
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
  /** One grade or two neighbouring ones. */
  grades: Grade[]
  stackRequired: string[]
  stackNice: string[]
  relocationHelp: boolean
  employmentTypes: EmploymentType[]
  benefits: VacancyBenefit[]
  /** Only candidates whose grade the test confirmed. */
  verifiedGradeOnly: boolean
  fspBestResult: FspResult | null
  fspDiscipline: string | null
  /** 0, 1, 3 or 5: «без опыта», «от года», «от 3», «от 5». */
  minExperienceYears: number | null
}

export type Reaction = 'like' | 'skip'

/**
 * Which cards a feed returns: everything except skipped ones, the ones not decided on yet
 * (swipe deck), or one of the lists of the user's own decisions. `matched` = liked and liked back.
 */
export type FeedView = 'all' | 'unseen' | 'liked' | 'matched' | 'skipped'

/** Sizes of the three decision lists. */
export type ReactionCountsDto = { liked: number; matched: number; skipped: number }

/** One card of the candidate's feed with the explanation of its position. */
export type VacancyMatchDto = {
  vacancy: VacancyDto
  /** 0..1; null when the feed is not personalised yet. */
  matchScore: number | null
  reasons: string[]
  reaction: Reaction | null
  /** Mutual interest: the vacancy is liked and its recruiter liked the candidate back. */
  matched: boolean
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
  reactionCounts: () => [...vacancyKeys.all, 'reaction-counts'] as const,
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
  /** Candidate: how many vacancies are liked, matched and skipped. */
  reactionCounts: () =>
    queryOptions({
      queryKey: vacancyKeys.reactionCounts(),
      queryFn: ({ signal }) =>
        http.get<ReactionCountsDto>('/vacancies/reactions/counts', { signal }),
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
