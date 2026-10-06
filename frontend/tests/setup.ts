import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, vi } from 'vitest'
import { sessionStore } from '@/entities/session'

afterEach(() => {
  cleanup()
  sessionStore.clear()
  window.sessionStorage.clear()
  window.localStorage.clear()
  vi.unstubAllGlobals()
})

// jsdom does not implement matchMedia; components only need the listener API.
if (!window.matchMedia) {
  window.matchMedia = (query: string) =>
    ({
      matches: false,
      media: query,
      onchange: null,
      addEventListener: () => {},
      removeEventListener: () => {},
      addListener: () => {},
      removeListener: () => {},
      dispatchEvent: () => false,
    }) as MediaQueryList
}
