import { act, render } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { HackerRain } from '@/shared/ui/hacker-rain/hacker-rain'

function glyphsOf(container: HTMLElement): string[] {
  return [...container.querySelectorAll('.hacker-rain__drop')].map((drop) => drop.textContent ?? '')
}

describe('HackerRain', () => {
  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
  })

  it('lifts one ASCII glyph per drop', () => {
    vi.spyOn(Math, 'random').mockReturnValue(0.5)
    vi.stubGlobal('matchMedia', () => ({ matches: false }))

    const view = render(<HackerRain count={5} />)
    const drops = view.container.querySelectorAll('.hacker-rain__drop')

    expect(view.container.querySelector('.hacker-rain')).toHaveAttribute('aria-hidden', 'true')
    expect(drops).toHaveLength(5)
    for (const drop of drops) {
      expect(drop.className).toContain('hacker-rain__drop--blue')
      const glyph = drop.textContent ?? ''
      expect(glyph).toHaveLength(1)
      const code = glyph.charCodeAt(0)
      expect(code).toBeGreaterThanOrEqual(33)
      expect(code).toBeLessThan(33 + 94)
    }
  })

  it('walks each glyph through ASCII noise, then lets it rest', async () => {
    vi.spyOn(Math, 'random').mockReturnValue(0)
    vi.stubGlobal('matchMedia', () => ({ matches: false }))
    vi.useFakeTimers()

    const view = render(<HackerRain count={4} />)
    expect(glyphsOf(view.container)).toEqual(['!', '!', '!', '!'])

    await act(() => vi.advanceTimersByTimeAsync(90))
    expect(glyphsOf(view.container)).toEqual(['"', '"', '"', '"'])

    await act(() => vi.advanceTimersByTimeAsync(90 * 8))
    expect(glyphsOf(view.container)).toEqual(['"', '"', '"', '"'])

    await act(() => vi.advanceTimersByTimeAsync(90))
    for (const glyph of glyphsOf(view.container)) {
      expect(glyph).toHaveLength(1)
      expect(glyph).not.toBe('"')
    }
  })

  it('renders nothing when motion is reduced', () => {
    vi.stubGlobal('matchMedia', () => ({ matches: true }))
    const view = render(<HackerRain />)
    expect(view.container.querySelector('.hacker-rain')).toBeNull()
  })
})
