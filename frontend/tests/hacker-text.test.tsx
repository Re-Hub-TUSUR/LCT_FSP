import { act, render } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { encodeQueues, HackerText } from '@/shared/ui/hacker-text/hacker-text'

describe('encodeQueues', () => {
  it('hides every glyph in noise and lets the left one finish first', () => {
    const queues = encodeQueues('A B', () => 0)

    expect(queues[0]?.[0]).toBe('!')
    expect(queues[0]?.at(-1)).toBe('A')
    expect(queues[0]?.slice(0, -1).every((glyph) => glyph !== 'A')).toBe(true)
    expect(queues[1]).toEqual([' '])
    expect(queues[2]?.at(-1)).toBe('B')
    expect(queues[0]?.length ?? 0).toBeLessThan(queues[2]?.length ?? 0)
  })

  it('spreads a long line so the tail does not land together', () => {
    const queues = encodeQueues('Я'.repeat(24), () => 0)
    const lengths = queues.map((queue) => queue.length)
    const tail = lengths.slice(-6)

    expect(new Set(tail).size).toBeGreaterThan(1)
    expect(Math.max(...lengths)).toBeLessThanOrEqual(25)
    for (let i = 1; i < lengths.length; i++) {
      expect(lengths[i]).toBeGreaterThanOrEqual(lengths[i - 1] ?? 0)
    }
  })
})

describe('HackerText', () => {
  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
  })

  it('starts as noise and decodes left to right', async () => {
    vi.spyOn(Math, 'random').mockReturnValue(0)
    vi.stubGlobal('matchMedia', () => ({ matches: false }))
    vi.useFakeTimers()

    const view = render(<HackerText text="Hi" />)
    const live = view.container.querySelector('[aria-hidden="true"]')

    expect(view.getByText('Hi', { selector: '.visually-hidden' })).toBeInTheDocument()
    expect(live).toHaveTextContent('!!')

    await act(() => vi.advanceTimersByTimeAsync(320))
    expect(live).toHaveTextContent('H!')

    await act(() => vi.advanceTimersByTimeAsync(120))
    expect(live).toHaveTextContent('Hi')
  })

  it('skips the scramble when motion is reduced', () => {
    vi.stubGlobal('matchMedia', () => ({ matches: true }))
    const view = render(<HackerText text="Hi" />)
    expect(view.container.querySelector('[aria-hidden="true"]')).toHaveTextContent('Hi')
  })
})
