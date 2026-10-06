import type { UserDto } from '@/entities/user/@x/session'

export type Session = {
  accessToken: string
  user: UserDto
}

// Access JWT lives in memory only. localStorage would let an XSS script steal it.
// A closed tab is restored by the httpOnly refresh cookie, which scripts cannot read.
const LEGACY_KEY = 'kadry.session'

type Listener = () => void

function forgetLegacyStorage() {
  if (typeof window === 'undefined') return
  window.localStorage.removeItem(LEGACY_KEY)
  window.sessionStorage.removeItem(LEGACY_KEY)
}

forgetLegacyStorage()

let current: Session | null = null
const listeners = new Set<Listener>()

function emit() {
  listeners.forEach((listener) => listener())
}

export const sessionStore = {
  getSnapshot: (): Session | null => current,
  subscribe(listener: Listener) {
    listeners.add(listener)
    return () => {
      listeners.delete(listener)
    }
  },
  set(next: Session) {
    forgetLegacyStorage()
    current = next
    emit()
  },
  clear() {
    forgetLegacyStorage()
    if (current === null) return
    current = null
    emit()
  },
}
