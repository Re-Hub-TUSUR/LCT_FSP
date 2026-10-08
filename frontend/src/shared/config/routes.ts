export const ROUTES = {
  landing: '/',
  auth: '/auth',
  employerAuth: '/auth/employer',
  candidateAuth: '/auth/candidate',
  profile: '/profile',
  profileInvitations: '/profile/invitations',
  profileResume: '/profile/resume',
  profileCategory: '/profile/category',
  profileSettings: '/profile/settings',
  profileCompany: '/profile/company',
  /** Registered as the redirect URI of the platform's FSP ID client. */
  fspCallback: '/profile/fsp/callback',
  vacancies: '/vacancies',
  vacancyNew: '/vacancies/new',
  vacancyEdit: '/vacancies/:vacancyId/edit',
  feed: '/feed',
  feedSwipe: '/feed/swipe',
  responses: '/responses',
  company: '/companies/:companyId',
  candidate: '/candidates/:candidateId',
  calendar: '/calendar',
  matching: '/matching',
  matchingProfile: '/matching/:kind/:id',
  testing: '/testing',
  testBuilder: '/testing/builder',
  admin: '/admin',
} as const

export type MatchingProfileKind = 'candidate' | 'company'

const segment = (value: string) => encodeURIComponent(value)

export const paths = {
  company: (companyId: string) => `/companies/${segment(companyId)}`,
  candidate: (candidateId: string) => `/candidates/${segment(candidateId)}`,
  vacancyEdit: (vacancyId: string) => `/vacancies/${segment(vacancyId)}/edit`,
  matchingProfile: (kind: MatchingProfileKind, id: string) => `/matching/${kind}/${segment(id)}`,
} as const
