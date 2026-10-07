import { render } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { Splash } from '@/shared/ui'

function addSplash() {
  const splash = document.createElement('div')
  splash.id = 'splash'
  document.body.append(splash)
  return splash
}

describe('Splash', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
    document.getElementById('splash')?.remove()
  })

  it('holds the static splash while mounted and removes it afterwards', () => {
    const splash = addSplash()
    const view = render(<Splash />)
    vi.runAllTimers()
    expect(splash).toBeInTheDocument()
    expect(splash).not.toHaveClass('splash--done')

    view.unmount()
    vi.advanceTimersByTime(0)
    expect(splash).toHaveClass('splash--done')
    vi.runAllTimers()
    expect(splash).not.toBeInTheDocument()
  })

  it('stays up when one gate hands over to the next', () => {
    const splash = addSplash()
    const view = render(<Splash key="session" />)
    view.rerender(<Splash key="route" />)
    vi.runAllTimers()
    expect(splash).toBeInTheDocument()
    expect(splash).not.toHaveClass('splash--done')

    view.unmount()
    vi.runAllTimers()
    expect(splash).not.toBeInTheDocument()
  })

  it('does nothing when the page has no splash', () => {
    const view = render(<Splash />)
    view.unmount()
    expect(() => vi.runAllTimers()).not.toThrow()
  })
})
