import { http } from '@/shared/api'
import type { UserDto, UserRole } from '@/entities/user/@x/session'

export type SignInPayload = {
  email: string
  password: string
}

export type SignUpPayload = SignInPayload & {
  role: Exclude<UserRole, 'admin'>
  /** Consent to personal data processing (152-ФЗ) is mandatory for registration. */
  personalDataConsent: true
}

export type TokenResponseDto = {
  accessToken: string
  tokenType: 'bearer'
  expiresIn: number
  user: UserDto
}

export type YandexStartPayload = {
  role: Exclude<UserRole, 'admin'>
  mode: 'sign-in' | 'sign-up'
  personalDataConsent: boolean
  redirectUri: string
}

export const sessionApi = {
  signIn: (payload: SignInPayload) => http.post<TokenResponseDto>('/auth/login', payload),
  signUp: (payload: SignUpPayload) => http.post<UserDto>('/auth/register', payload),
  verifyEmail: (payload: { email: string; code: string }) =>
    http.post<void>('/auth/verify-email', payload),
  resendVerification: (payload: { email: string }) =>
    http.post<void>('/auth/resend-verification', payload),
  /** Cookie-only. A 401 means there is no session to restore. */
  refresh: () => http.post<TokenResponseDto>('/auth/refresh', undefined, { skipAuthRefresh: true }),
  /** The admin subdomain already checked the browser password. */
  adminGate: () =>
    http.post<TokenResponseDto>('/auth/admin-gate', undefined, { skipAuthRefresh: true }),
  /** 404 when the Yandex app is not configured: the button stays hidden. */
  yandexStatus: () => http.get<{ enabled: true }>('/auth/yandex'),
  yandexStart: (payload: YandexStartPayload) =>
    http.post<{ authorizeUrl: string }>('/auth/yandex/start', payload),
  yandexCallback: (payload: { code: string; state: string }) =>
    http.post<TokenResponseDto & { created: boolean }>('/auth/yandex/callback', payload, {
      skipAuthRefresh: true,
    }),
  logout: () => http.post<void>('/auth/logout', undefined, { skipAuthRefresh: true }),
}
