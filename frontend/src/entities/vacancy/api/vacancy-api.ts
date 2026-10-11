import { queryOptions } from '@tanstack/react-query'
import { http } from '@/shared/api'
import type { OptionCountDto, Paginated, PaginationParams, SalaryRangeDto } from '@/shared/api'
import type { CategoryDto, Grade, SpecializationCode } from '@/entities/category/@x/vacancy'
import type { EmploymentType, FspResult, VacancyBenefit, WorkFormat } from '..'

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
  cityId?: number | null
  cityRegion?: string | null
  cityCountryCode?: string | null
  cityLatitude?: number | null
  cityLongitude?: number | null
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

/** The recruiter's vacancy form; an edit replaces the vacancy as a whole. */
export type VacancyWrite = {
  title: string
  description: string
  specialization: SpecializationCode
  grades: Grade[]
  stackRequired: string[]
  stackNice: string[]
  salary: SalaryRangeDto
  workFormat: WorkFormat
  /** Required for office and hybrid work: the place from the city list. */
  city: string | null
  cityId: number | null
  relocationHelp: boolean
  employmentTypes: EmploymentType[]
  benefits: VacancyBenefit[]
  verifiedGradeOnly: boolean
  fspBestResult: FspResult | null
  fspDiscipline: string | null
  minExperienceYears: number
  /** False: a draft only the company sees. */
  publish: boolean
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

/** profile: the candidate's specializations and grades, best fit first; free: all, newest. */
export type FeedMode = 'profile' | 'free'

/** The candidate's feed filters. «Подбор по профилю» fills them in from the profile. */
export type VacancyFiltersDto = {
  /** The top of the vacancy's range reaches it. */
  salaryMin: number | null
  /** Remote vacancies fit from anywhere; office and hybrid ones need one of `cities`. */
  workFormats: WorkFormat[]
  cities: string[]
  /** Also office and hybrid vacancies elsewhere that help to relocate. */
  relocation: boolean
  employmentTypes: EmploymentType[]
  stack: string[]
  nice: string[]
  benefits: VacancyBenefit[]
  accredited: boolean
}

/** Query parameters of the feed and of its counts. */
export type VacancyFeedFilterParams = {
  view?: FeedView
  mode?: FeedMode
  salaryMin?: number
  workFormat?: WorkFormat[]
  city?: string[]
  relocation?: boolean
  employment?: EmploymentType[]
  stack?: string[]
  nice?: string[]
  benefit?: VacancyBenefit[]
  accredited?: boolean
}

export type VacancyFeedParams = PaginationParams & VacancyFeedFilterParams

export type VacancyRelaxationKind =
  'salary' | 'work_formats' | 'employment' | 'cities' | 'stack' | 'benefit' | 'accredited' | 'mode'

/** A filter to loosen when nothing matched: `value` is the lowered salary, the technology or
 * the condition. */
export type VacancyRelaxationDto = {
  kind: VacancyRelaxationKind
  value: string | null
  count: number
}

/** How many vacancies each option leaves, the other filters staying as they are. */
export type VacancyFacetsDto = {
  total: number
  count: number
  /** The option added to the ones chosen in its group. */
  workFormats: OptionCountDto[]
  employmentTypes: OptionCountDto[]
  benefits: OptionCountDto[]
  accredited: number
  /** Vacancies of the mode in each city and asking for each technology. */
  cities: OptionCountDto[]
  stack: OptionCountDto[]
  relaxations: VacancyRelaxationDto[]
}

/** The candidate's feed to save: the mode and the filters as they are now. */
export type VacancySearchSaveDto = {
  title?: string
  mode: FeedMode
  filters: VacancyFiltersDto
}

/** A saved search: how many vacancies it finds now and how many of them were not seen. */
export type SavedVacancySearchDto = {
  id: string
  title: string
  summary: string
  mode: FeedMode
  filters: VacancyFiltersDto
  count: number
  newCount: number
  createdAt: string
}

export type VacancyFeedPresetsDto = {
  /** False until the candidate has a category: only the free search then. */
  personalized: boolean
  /** What «Подбор по профилю» fills in and how many vacancies that leaves. */
  profile: VacancyFiltersDto | null
  profileCount: number
  category: CategoryDto | null
  /** Every published vacancy of the view. */
  freeCount: number
}

export type VacancyListParams = PaginationParams & {
  /** Only the vacancies of this company. */
  companyId?: string
  search?: string
  specialization?: SpecializationCode
  grade?: Grade
  workFormat?: WorkFormat
}

export const vacancyKeys = {
  all: ['vacancies'] as const,
  list: (params: VacancyListParams) => [...vacancyKeys.all, 'list', params] as const,
  feed: (params: VacancyFeedParams) => [...vacancyKeys.all, 'feed', params] as const,
  feedFacets: (params: VacancyFeedFilterParams) =>
    [...vacancyKeys.all, 'feed-facets', params] as const,
  feedPresets: (view: FeedView) => [...vacancyKeys.all, 'feed-presets', view] as const,
  savedSearches: () => [...vacancyKeys.all, 'saved-searches'] as const,
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
  /** Counts next to the feed's filter options and the ways out of an empty feed. */
  feedFacets: (params: VacancyFeedFilterParams) =>
    queryOptions({
      queryKey: vacancyKeys.feedFacets(params),
      queryFn: ({ signal }) =>
        http.get<VacancyFacetsDto>('/vacancies/feed/facets', { query: params, signal }),
    }),
  /** The feed's modes and the filters the profile fills in. */
  feedPresets: (view: FeedView = 'all') =>
    queryOptions({
      queryKey: vacancyKeys.feedPresets(view),
      queryFn: ({ signal }) =>
        http.get<VacancyFeedPresetsDto>('/vacancies/feed/presets', { query: { view }, signal }),
    }),
  /** The candidate's saved searches with their new vacancies. */
  savedSearches: () =>
    queryOptions({
      queryKey: vacancyKeys.savedSearches(),
      queryFn: ({ signal }) =>
        http.get<SavedVacancySearchDto[]>('/vacancies/feed/saved-searches', { signal }),
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
  create: (payload: VacancyWrite) => http.post<VacancyDto>('/vacancies', payload),
  update: (id: string, payload: VacancyWrite) =>
    http.patch<VacancyDto>(`/vacancies/${id}`, payload),
  saveSearch: (payload: VacancySearchSaveDto) =>
    http.post<SavedVacancySearchDto>('/vacancies/feed/saved-searches', payload),
  /** Opened: every vacancy the search finds now counts as seen. */
  openSearch: (id: string) =>
    http.post<SavedVacancySearchDto>(`/vacancies/feed/saved-searches/${id}/seen`),
  deleteSearch: (id: string) => http.delete<void>(`/vacancies/feed/saved-searches/${id}`),
  react: (id: string, kind: Reaction) => http.put<unknown>(`/vacancies/${id}/reaction`, { kind }),
  clearReaction: (id: string) => http.delete<void>(`/vacancies/${id}/reaction`),
}
