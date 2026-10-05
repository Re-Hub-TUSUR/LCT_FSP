export const ROUTES = {
  landing: '/',
  auth: '/auth',
  employerAuth: '/auth/employer',
  candidateAuth: '/auth/candidate',
  profile: '/profile',
  vacancies: '/vacancies',
  feed: '/feed',
  feedSwipe: '/feed/swipe',
  company: '/companies/:companyId',
  candidate: '/candidates/:candidateId',
  calendar: '/calendar',
  matching: '/matching',
  matchingProfile: '/matching/:kind/:id',
  testing: '/testing',
  admin: '/admin',
} as const

export type MatchingProfileKind = 'candidate' | 'company'

const segment = (value: string) => encodeURIComponent(value)

export const paths = {
  company: (companyId: string) => `/companies/${segment(companyId)}`,
  candidate: (candidateId: string) => `/candidates/${segment(candidateId)}`,
  matchingProfile: (kind: MatchingProfileKind, id: string) => `/matching/${kind}/${segment(id)}`,
} as const
