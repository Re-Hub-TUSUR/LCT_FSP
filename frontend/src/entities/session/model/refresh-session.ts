import { ApiError } from '@/shared/api'
import { sessionApi } from '../api/session-api'
import { sessionStore } from './session-store'

let flight: Promise<string | null> | null = null

/** One in-flight refresh for the tab. Parallel 401s and a remount share it. */
export function refreshSession(): Promise<string | null> {
  if (flight) return flight
  flight = sessionApi
    .refresh()
    .then((token) => {
      sessionStore.set({ accessToken: token.accessToken, user: token.user })
      return token.accessToken
    })
    .catch((error: unknown) => {
      if (error instanceof ApiError && error.status === 401) sessionStore.clear()
      return null
    })
    .finally(() => {
      flight = null
    })
  return flight
}
