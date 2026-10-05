import { useSyncExternalStore } from 'react'
import { sessionStore } from './session-store'

export function useSession() {
  const session = useSyncExternalStore(
    sessionStore.subscribe,
    sessionStore.getSnapshot,
    sessionStore.getSnapshot,
  )
  return {
    session,
    user: session?.user ?? null,
    isAuthenticated: session !== null,
  }
}
