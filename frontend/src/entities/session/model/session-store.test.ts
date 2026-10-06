import { describe, expect, it, vi } from 'vitest'
import { sessionStore } from './session-store'

const session = {
  accessToken: 't',
  user: {
    id: '1',
    email: 'a@b.ru',
    role: 'candidate' as const,
    isEmailVerified: false,
    createdAt: '2026-01-01T00:00:00Z',
  },
}

describe('sessionStore', () => {
  it('keeps the session in memory and out of web storage', () => {
    const listener = vi.fn<() => void>()
    const unsubscribe = sessionStore.subscribe(listener)
    window.localStorage.setItem('kadry.session', '{"accessToken":"stolen"}')

    sessionStore.set(session)
    expect(sessionStore.getSnapshot()).toEqual(session)
    expect(window.localStorage.getItem('kadry.session')).toBeNull()
    expect(window.sessionStorage.getItem('kadry.session')).toBeNull()

    sessionStore.clear()
    expect(sessionStore.getSnapshot()).toBeNull()
    expect(listener).toHaveBeenCalledTimes(2)

    unsubscribe()
  })
})
