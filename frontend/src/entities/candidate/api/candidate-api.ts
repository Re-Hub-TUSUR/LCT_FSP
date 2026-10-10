import { queryOptions } from '@tanstack/react-query'
import { http } from '@/shared/api'
import type { OptionCountDto, Paginated, PaginationParams } from '@/shared/api'
import type { AssessmentStatus } from '@/entities/assessment/@x/candidate'
import type { CategoryDto, Grade, SpecializationCode } from '@/entities/category/@x/candidate'
import type {
  EmploymentType,
  FeedView,
  FspResult,
  Reaction,
  ReactionCountsDto,
  WorkFormat,
} from '@/entities/vacancy/@x/candidate'
import type { FspSync, JobStatus } from '../model/job-status'

/** A place of work; months are "YYYY-MM", no end = still there. */
export type ExperienceEntryDto = {
  company: string
  position: string
  start: string
  end: string | null
  stack: string[]
}

export type EducationEntryDto = {
  institution: string
  specialty: string | null
  year: number | null
}

export type FspDiscipline = 'algorithmic' | 'product' | 'security' | 'robotics' | 'uav'

export type FspEventKind = 'championship' | 'cup' | 'hackathon' | 'olympiad'
export type FspOutcome = 'winner' | 'prizewinner' | 'finalist' | 'participant'
export type FspParticipation = 'individual' | 'team'
export type FspTitleKind = 'rank_3' | 'rank_2' | 'rank_1' | 'kms' | 'ms' | 'msmk' | 'zms'

/** A result confirmed by the FSP registry. */
export type FspAchievementDto = {
  eventName: string
  eventKind: FspEventKind
  year: number
  /** Null = took part without a prize place. */
  place: number | null
  result: FspOutcome
  participation: FspParticipation
  teamName: string | null
  discipline: FspDiscipline
  level: 'regional' | 'national' | 'international'
}

/** A sport rank or title of the federation (разряд, КМС, МС…). */
export type FspSportTitleDto = {
  kind: FspTitleKind
  discipline: FspDiscipline
  awardedYear: number
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
  /** The grade was confirmed by a beta test and is provisional. */
  gradeBeta?: boolean
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
  fspTitles: FspSportTitleDto[]
  fspLinked: boolean
  resumes?: ResumeDto[]
  hasPhoto?: boolean
  contacts: CandidateContactsDto | null
  jobStatus: JobStatus
  employmentTypes: EmploymentType[]
  experienceEntries: ExperienceEntryDto[]
  noExperience: boolean
  education: EducationEntryDto[]
  githubUrl: string | null
  /** Under 18: the employer sees it, the birth date itself stays private. */
  isMinor: boolean
  lastActiveAt: string | null
  /**
   * For an employer on a profile page: mutual interest (the recruiter saved the candidate, the
   * candidate liked a vacancy of the company). Absent where it is not computed.
   */
  matched?: boolean | null
}

/** Cabinet view: the search switch and the FSP ID link with its sync state. */
export type OwnCandidateDto = CandidateDto & {
  searching: boolean
  /** Confirmed by FSP ID sign-in, never typed by the candidate. */
  fspMemberId: string | null
  /** Kept before a grade exists, so the resume can be reopened. */
  specialization: string | null
  birthDate: string | null
  profileDisplayConsent: boolean
  fspSync: FspSync | null
  fspLinkedAt?: string | null
  /** Last successful import from the FSP registry. */
  fspSyncedAt?: string | null
  /** The registry did not answer on the last import; the link stays. */
  fspSyncError?: string | null
}

export type FspAuthorizeDto = { authorizeUrl: string }

/** What FSP ID returns to `/profile/fsp/callback`. */
export type FspLinkRequest = { code: string; state: string }

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
  relocationReady?: boolean
  birthDate?: string | null
  jobStatus?: JobStatus
  employmentTypes?: EmploymentType[]
  experienceEntries?: ExperienceEntryDto[]
  noExperience?: boolean
  education?: EducationEntryDto[]
  githubUrl?: string | null
  profileDisplayConsent?: boolean
  fspSync?: FspSync | null
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
  /** Portrait found in the file: base64 JPEG. */
  photo: string | null
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

/** The recruiter's filters. Selecting a vacancy fills them in from its requirements. */
export type CandidateFiltersDto = {
  specializations: SpecializationCode[]
  grades: Grade[]
  verifiedOnly: boolean
  /** False: no FSP results; true: some result, at least `fspResult` in `fspDiscipline`. */
  hasFsp: boolean | null
  fspResult: FspResult | null
  fspDiscipline: FspDiscipline | null
  experienceMin: number | null
  /** «Обязательно»: every technology. «Будет плюсом»: ranks higher, filters nobody. */
  stack: string[]
  nice: string[]
  salaryMin: number | null
  salaryMax: number | null
  /** Remote needs no city; office and hybrid need one of `cities` or readiness to relocate. */
  workFormats: WorkFormat[]
  cities: string[]
  relocation: boolean
  employmentTypes: EmploymentType[]
  jobStatuses: JobStatus[]
  /** Signed in within this many days. */
  activeDays: number | null
}

/** Query parameters of the search and of its counts. */
export type CandidateFilterParams = {
  q?: string
  view?: FeedView
  specialization?: SpecializationCode[]
  grade?: Grade[]
  verifiedOnly?: boolean
  hasFspAchievements?: boolean
  fspResult?: FspResult
  fspDiscipline?: FspDiscipline
  experienceMin?: number
  stack?: string[]
  nice?: string[]
  salaryMin?: number
  salaryMax?: number
  workFormat?: WorkFormat[]
  city?: string[]
  relocation?: boolean
  employment?: EmploymentType[]
  jobStatus?: JobStatus[]
  activeDays?: number
}

export type CandidateSearchParams = PaginationParams &
  CandidateFilterParams & {
    vacancyId?: string
    sort?: CandidateSort
  }

export type CandidateRelaxationKind =
  | 'stack'
  | 'salary_max'
  | 'salary_min'
  | 'grades'
  | 'specializations'
  | 'verified'
  | 'fsp_result'
  | 'fsp_discipline'
  | 'fsp'
  | 'experience'
  | 'work_formats'
  | 'relocation'
  | 'cities'
  | 'employment'
  | 'job_statuses'
  | 'active'

/** A filter to loosen when nobody matched; `value` is the technology for `stack`. */
export type CandidateRelaxationDto = {
  kind: CandidateRelaxationKind
  value: string | null
  count: number
}

/** How many candidates each option leaves, the other filters staying as they are. */
export type CandidateFacetsDto = {
  /** Candidates of the view and the text query before the filters. */
  total: number
  /** Candidates matching every filter. */
  count: number
  /** The option chosen alone in its group. */
  specializations: OptionCountDto[]
  grades: OptionCountDto[]
  verified: number
  fsp: number
  fspResults: OptionCountDto[]
  fspDisciplines: OptionCountDto[]
  /** «1», «3», «5» years and more. */
  experience: OptionCountDto[]
  workFormats: OptionCountDto[]
  /** Each city alone, without relocation; the most frequent first. */
  cities: OptionCountDto[]
  relocation: number
  employmentTypes: OptionCountDto[]
  jobStatuses: OptionCountDto[]
  active: number
  /** Matching candidates knowing each technology of the bank, the most frequent first. */
  stack: OptionCountDto[]
  /** Up to three, only when nobody matched. */
  relaxations: CandidateRelaxationDto[]
}

/** An own vacancy in the search's mode list with its requirements as filters. */
export type VacancyPresetDto = {
  vacancyId: string
  title: string
  workFormat: WorkFormat
  city: string | null
  salaryTo: number
  published: boolean
  filters: CandidateFiltersDto
  count: number
}

/** The recruiter's search to save: what the list shows now. */
export type CandidateSearchSaveDto = {
  title?: string
  filters: CandidateFiltersDto
  text?: string | null
  vacancyId?: string | null
}

/** A saved search: how many candidates it finds now and how many of them were not seen. */
export type SavedCandidateSearchDto = {
  id: string
  title: string
  summary: string
  filters: CandidateFiltersDto
  text: string | null
  vacancyId: string | null
  count: number
  newCount: number
  createdAt: string
}

export type CandidatePresetsDto = {
  /** Free search: every candidate of the view. */
  total: number
  vacancies: VacancyPresetDto[]
}

export const candidateKeys = {
  all: ['candidates'] as const,
  detail: (id: string) => [...candidateKeys.all, 'detail', id] as const,
  mine: () => [...candidateKeys.all, 'mine'] as const,
  search: (params: CandidateSearchParams) => [...candidateKeys.all, 'search', params] as const,
  facets: (params: CandidateFilterParams) => [...candidateKeys.all, 'facets', params] as const,
  presets: (view: FeedView) => [...candidateKeys.all, 'presets', view] as const,
  savedSearches: () => [...candidateKeys.all, 'saved-searches'] as const,
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
  /** Counts next to the search's filter options and the ways out of an empty list. */
  facets: (params: CandidateFilterParams) =>
    queryOptions({
      queryKey: candidateKeys.facets(params),
      queryFn: ({ signal }) =>
        http.get<CandidateFacetsDto>('/candidates/facets', { query: params, signal }),
    }),
  /** Own vacancies as ready-made filters. */
  presets: (view: FeedView = 'all') =>
    queryOptions({
      queryKey: candidateKeys.presets(view),
      queryFn: ({ signal }) =>
        http.get<CandidatePresetsDto>('/candidates/presets', { query: { view }, signal }),
    }),
  /** The recruiter's saved searches with their new candidates. */
  savedSearches: () =>
    queryOptions({
      queryKey: candidateKeys.savedSearches(),
      queryFn: ({ signal }) =>
        http.get<SavedCandidateSearchDto[]>('/candidates/saved-searches', { signal }),
    }),
  mine: () =>
    queryOptions({
      queryKey: candidateKeys.mine(),
      // `null` until the first resume is saved.
      queryFn: ({ signal }) => http.get<OwnCandidateDto | null>('/candidates/me', { signal }),
      staleTime: 30_000,
    }),
}

export const candidateApi = {
  saveSearch: (payload: CandidateSearchSaveDto) =>
    http.post<SavedCandidateSearchDto>('/candidates/saved-searches', payload),
  /** Opened: every candidate the search finds now counts as seen. */
  openSearch: (id: string) =>
    http.post<SavedCandidateSearchDto>(`/candidates/saved-searches/${id}/seen`),
  deleteSearch: (id: string) => http.delete<void>(`/candidates/saved-searches/${id}`),
  react: (id: string, kind: Reaction, vacancyId?: string) =>
    http.put<unknown>(`/candidates/${id}/reaction`, { kind, vacancyId }),
  clearReaction: (id: string) => http.delete<void>(`/candidates/${id}/reaction`),
  saveResume: (payload: CandidateProfileUpdate) =>
    http.patch<OwnCandidateDto>('/candidates/me', payload),
  /** An existing profile: the server changes only the fields that were sent. */
  updateProfile: (patch: Partial<CandidateProfileUpdate>) =>
    http.patch<OwnCandidateDto>('/candidates/me', patch),
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
  /** The resume as a PDF: what the viewer sees on the site, contacts only when allowed. */
  resumePdf: (candidateId: string) => http.blob(`/candidates/${candidateId}/resume.pdf`),
  uploadResume: (file: File) => {
    const body = new FormData()
    body.append('file', file)
    return http.post<ResumeDraftDto>('/candidates/me/resume', body)
  },
  setJobStatus: (jobStatus: JobStatus) =>
    http.patch<OwnCandidateDto>('/candidates/me/searching', { jobStatus }),
  /** Starts the FSP ID sign-in (OIDC + PKCE): the browser goes to the returned URL. */
  authorizeFsp: (redirectUri: string) =>
    http.post<FspAuthorizeDto>('/fsp-id/authorize', { redirectUri }),
  linkFsp: (answer: FspLinkRequest) =>
    http.post<OwnCandidateDto>('/candidates/me/fsp-link', answer),
  /** Re-reads the FSP registry without a new sign-in. */
  syncFsp: () => http.post<OwnCandidateDto>('/candidates/me/fsp-sync'),
  unlinkFsp: () => http.delete<OwnCandidateDto>('/candidates/me/fsp-link'),
}
