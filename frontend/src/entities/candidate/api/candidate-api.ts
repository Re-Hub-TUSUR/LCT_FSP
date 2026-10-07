import { queryOptions } from '@tanstack/react-query'
import { http } from '@/shared/api'
import type { Paginated, PaginationParams } from '@/shared/api'
import type { AssessmentStatus } from '@/entities/assessment/@x/candidate'
import type { CategoryDto, Grade, SpecializationCode } from '@/entities/category/@x/candidate'
import type {
  FeedView,
  Reaction,
  ReactionCountsDto,
  WorkFormat,
} from '@/entities/vacancy/@x/candidate'

export type FspDiscipline = 'algorithmic' | 'product' | 'security' | 'robotics' | 'uav'

export type FspAchievementDto = {
  eventName: string
  year: number
  /** Null = took part without a prize place. */
  place: number | null
  discipline: FspDiscipline
  level: 'regional' | 'national' | 'international'
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
  about: string | null
  category: CategoryDto | null
  /** False: the test was skipped, the grade is self-declared. */
  gradeVerified: boolean
  assessmentScore: number | null
  /** Platform grade test: passed, failed or never taken. */
  assessmentStatus: AssessmentStatus
  stack: string[]
  softSkills: string[]
  experienceYears: number | null
  englishLevel: string | null
  city: string | null
  relocationReady: boolean
  workFormats: WorkFormat[]
  salaryExpectation: number | null
  /** Empty list is a valid, explicitly handled state: candidate has no FSP history. */
  fspAchievements: FspAchievementDto[]
  fspLinked: boolean
  resumes?: ResumeDto[]
  hasPhoto?: boolean
  contacts: CandidateContactsDto | null
  /**
   * For an employer on a profile page: mutual interest (the recruiter saved the candidate, the
   * candidate liked a vacancy of the company). Absent where it is not computed.
   */
  matched?: boolean | null
}

/** Cabinet view: the search switch and the FSP id the candidate entered. */
export type OwnCandidateDto = CandidateDto & {
  searching: boolean
  fspMemberId: string | null
  /** Kept before a grade exists, so the resume can be reopened. */
  specialization: string | null
}

export type ResumeDto = {
  id: string
  headline: string | null
  specialization: string | null
  stack: string[]
  softSkills: string[]
  about: string | null
  experienceYears: number | null
  isPrimary: boolean
}

export type ResumeCreate = {
  headline: string
  specialization: string
  stack: string[]
  softSkills: string[]
  about: string | null
  experienceYears: number
}

export type CandidateProfileUpdate = {
  displayName: string
  headline: string
  about: string | null
  stack: string[]
  softSkills: string[]
  experienceYears: number
  city: string
  workFormats: WorkFormat[]
  salaryExpectation: number | null
  phone: string | null
  telegram: string | null
  specialization: string
}

/** Fields recognised in an uploaded resume. Nothing is saved until the candidate saves the form. */
export type ResumeDraftDto = {
  displayName: string | null
  headline: string | null
  specialization: string | null
  city: string | null
  experienceYears: number | null
  workFormats: WorkFormat[]
  stack: string[]
  softSkills: string[]
  about: string | null
  salaryExpectation: number | null
  phone: string | null
  telegram: string | null
}

/** One card of the recruiter's feed with the explanation of its position. */
export type CandidateMatchDto = {
  candidate: CandidateDto
  /** Fit to the selected vacancy, 0..1; null without a vacancy. */
  matchScore: number | null
  /** Test + FSP results, 0..1: the order inside a category. */
  profileStrength: number
  reasons: string[]
  reaction: Reaction | null
  /** Mutual interest: the recruiter liked the candidate, who liked a vacancy of the company. */
  matched: boolean
}

export type CandidateSearchDto = Paginated<CandidateMatchDto> & {
  engine: 'elasticsearch' | 'database'
}

export type CandidateSort = 'relevance' | 'assessment' | 'salary' | 'experience'

export type CandidateSearchParams = PaginationParams & {
  q?: string
  specialization?: SpecializationCode
  grade?: Grade[]
  stack?: string[]
  hasFspAchievements?: boolean
  verifiedOnly?: boolean
  workFormat?: WorkFormat[]
  city?: string
  salaryMax?: number
  vacancyId?: string
  view?: FeedView
  sort?: CandidateSort
}

export const candidateKeys = {
  all: ['candidates'] as const,
  detail: (id: string) => [...candidateKeys.all, 'detail', id] as const,
  mine: () => [...candidateKeys.all, 'mine'] as const,
  search: (params: CandidateSearchParams) => [...candidateKeys.all, 'search', params] as const,
  reactionCounts: () => [...candidateKeys.all, 'reaction-counts'] as const,
}

export const candidateQueries = {
  detail: (id: string) =>
    queryOptions({
      queryKey: candidateKeys.detail(id),
      queryFn: ({ signal }) => http.get<CandidateDto>(`/candidates/${id}`, { signal }),
      enabled: Boolean(id),
    }),
  /** Employer: how many candidates are liked, matched and skipped. */
  reactionCounts: () =>
    queryOptions({
      queryKey: candidateKeys.reactionCounts(),
      queryFn: ({ signal }) =>
        http.get<ReactionCountsDto>('/candidates/reactions/counts', { signal }),
    }),
  /** Recruiter's search over the categorised bank (Elasticsearch on the backend). */
  search: (params: CandidateSearchParams) =>
    queryOptions({
      queryKey: candidateKeys.search(params),
      queryFn: ({ signal }) =>
        http.get<CandidateSearchDto>('/candidates', { query: params, signal }),
    }),
  mine: () =>
    queryOptions({
      queryKey: candidateKeys.mine(),
      queryFn: ({ signal }) => http.get<OwnCandidateDto>('/candidates/me', { signal }),
      staleTime: 30_000,
    }),
}

export const candidateApi = {
  react: (id: string, kind: Reaction, vacancyId?: string) =>
    http.put<unknown>(`/candidates/${id}/reaction`, { kind, vacancyId }),
  clearReaction: (id: string) => http.delete<void>(`/candidates/${id}/reaction`),
  saveResume: (payload: CandidateProfileUpdate) =>
    http.patch<OwnCandidateDto>('/candidates/me', payload),
  addResume: (payload: ResumeCreate) =>
    http.post<OwnCandidateDto>('/candidates/me/resumes', payload),
  makePrimary: (resumeId: string) =>
    http.post<OwnCandidateDto>(`/candidates/me/resumes/${resumeId}/primary`),
  uploadPhoto: (file: File) => {
    const body = new FormData()
    body.append('file', file)
    return http.post<OwnCandidateDto>('/candidates/me/photo', body)
  },
  photo: (candidateId: string) => http.blob(`/candidates/${candidateId}/photo`),
  uploadResume: (file: File) => {
    const body = new FormData()
    body.append('file', file)
    return http.post<ResumeDraftDto>('/candidates/me/resume', body)
  },
  setSearching: (searching: boolean) =>
    http.patch<OwnCandidateDto>('/candidates/me/searching', { searching }),
  linkFsp: (fspMemberId: string) =>
    http.post<OwnCandidateDto>('/candidates/me/fsp-link', { fspMemberId }),
  unlinkFsp: () => http.delete<OwnCandidateDto>('/candidates/me/fsp-link'),
}
