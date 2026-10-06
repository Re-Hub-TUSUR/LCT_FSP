import { sessionApi } from '../api/session-api'
import { sessionStore } from './session-store'

/** Revokes the refresh cookie, then drops the access token on this device. */
export async function signOut(): Promise<void> {
  try {
    await sessionApi.logout()
  } catch {
    // The local session still has to go, even if the network call fails.
  }
  sessionStore.clear()
}
