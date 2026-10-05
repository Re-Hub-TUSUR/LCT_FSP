import type { UserDto } from '@/entities/user/@x/session'

export type Session = {
  accessToken: string
  user: UserDto
}

// MVP trade-off: the short-lived access token lives in sessionStorage so a reload keeps the user
// signed in. Planned replacement: refresh token in an httpOnly cookie (see docs/ARCHITECTURE.md).
const STORAGE_KEY = 'kadry.session'

type Listener = () => void

function readPersisted(): Session | null {
  if (typeof window === 'undefined') return null
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as Session) : null
  } catch {
    return null
  }
}

let current: Session | null = readPersisted()
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
    current = next
    window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(next))
    emit()
  },
  clear() {
    if (current === null) return
    current = null
    window.sessionStorage.removeItem(STORAGE_KEY)
    emit()
  },
}
