import { afterEach, describe, expect, it, vi } from 'vitest'
import { isStaleChunkError, reloadForNewBuild } from './stale-build'

describe('stale build', () => {
  afterEach(() => {
    sessionStorage.clear()
    vi.unstubAllGlobals()
  })

  it('tells a missing chunk from any other error', () => {
    const chrome = new TypeError(
      'Failed to fetch dynamically imported module: https://site/assets/vacancies-CWRT5tE9.js',
    )
    expect(isStaleChunkError(chrome)).toBe(true)
    expect(isStaleChunkError(new TypeError('error loading dynamically imported module'))).toBe(true)
    expect(isStaleChunkError(new TypeError('Importing a module script failed.'))).toBe(true)
    expect(isStaleChunkError(new Error('Cannot read properties of undefined'))).toBe(false)
    expect(isStaleChunkError('Failed to fetch dynamically imported module')).toBe(false)
  })

  it('reloads once and leaves a repeated failure on screen', () => {
    const reload = vi.fn<() => void>()
    vi.stubGlobal('location', { ...window.location, reload })

    expect(reloadForNewBuild()).toBe(true)
    expect(reloadForNewBuild()).toBe(false)
    expect(reload).toHaveBeenCalledTimes(1)
  })
})
