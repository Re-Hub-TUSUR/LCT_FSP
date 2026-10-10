import { ApiError } from '@/shared/api'
import { sessionApi } from '../api/session-api'
import { sessionStore } from './session-store'

let flight: Promise<string | null> | null = null

const RETRY_AFTER_MS = 400

/**
 * The server rotates the cookie and lets only one request use it. Another tab opened at the same
 * moment loses that race with a 401; by then the winner has stored the new cookie, so one more
 * try succeeds.
 */
async function refreshOnce() {
  try {
    return await sessionApi.refresh()
  } catch (error) {
    if (!(error instanceof ApiError && error.status === 401)) throw error
    await new Promise((resolve) => setTimeout(resolve, RETRY_AFTER_MS))
    return sessionApi.refresh()
  }
}

/** One in-flight refresh for the tab. Parallel 401s and a remount share it. */
export function refreshSession(): Promise<string | null> {
  if (flight) return flight
  flight = refreshOnce()
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
