import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createDraftSaver } from './draft-saver'

describe('createDraftSaver', () => {
  beforeEach(() => vi.useFakeTimers())
  afterEach(() => vi.useRealTimers())

  it('saves the newest text after a pause in typing', async () => {
    const save = vi.fn<(id: string, value: string) => Promise<void>>().mockResolvedValue()
    const saver = createDraftSaver(save)

    saver.change('t1', 'a')
    await vi.advanceTimersByTimeAsync(600)
    saver.change('t1', 'ab')
    await vi.advanceTimersByTimeAsync(600)
    expect(save).not.toHaveBeenCalled()

    await vi.advanceTimersByTimeAsync(400)
    expect(save.mock.calls).toEqual([['t1', 'ab']])
  })

  it('saves during non-stop typing instead of waiting for a pause that never comes', async () => {
    const save = vi.fn<(id: string, value: string) => Promise<void>>().mockResolvedValue()
    const saver = createDraftSaver(save)

    // A key every 300 ms for 12 seconds: the idle timer never fires.
    for (let typed = 1; typed <= 40; typed += 1) {
      saver.change('t1', 'x'.repeat(typed))
      await vi.advanceTimersByTimeAsync(300)
    }

    expect(save.mock.calls.length).toBeGreaterThanOrEqual(2)
    // Nothing older than five seconds is left unsaved.
    expect(save.mock.calls.at(-1)?.[1].length).toBeGreaterThanOrEqual(40 - 17)
  })

  it('flushes every changed answer at once and reports a failed save', async () => {
    const onFailed = vi.fn<(error: unknown) => void>()
    const save = vi
      .fn<(id: string, value: string) => Promise<void>>()
      .mockResolvedValueOnce()
      .mockResolvedValueOnce()
      .mockRejectedValueOnce(new Error('offline'))
    const saver = createDraftSaver(save, { onFailed })

    saver.change('t1', 'code')
    saver.change('t2', 'text')
    await saver.flush()
    expect(save.mock.calls).toEqual([
      ['t1', 'code'],
      ['t2', 'text'],
    ])

    // Nothing is pending after a flush: the timers have nothing to send.
    await vi.advanceTimersByTimeAsync(10_000)
    expect(save).toHaveBeenCalledTimes(2)

    saver.change('t1', 'more')
    await vi.advanceTimersByTimeAsync(1000)
    expect(onFailed).toHaveBeenCalledWith(new Error('offline'))
  })
})
