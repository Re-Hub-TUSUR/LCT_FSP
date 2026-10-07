import { describe, expect, it } from 'vitest'
import { createTaskClock } from './task-clock'

function setup() {
  let time = 0
  const reports: [string, number][] = []
  const clock = createTaskClock(
    (taskId, seconds) => {
      reports.push([taskId, seconds])
      return Promise.resolve()
    },
    () => time,
  )
  return { clock, reports, wait: (ms: number) => (time += ms) }
}

describe('task clock', () => {
  it('reports a task when the candidate moves to another one', () => {
    const { clock, reports, wait } = setup()
    clock.show('a')
    wait(5000)
    clock.show('b')
    wait(2000)
    clock.show('a')
    expect(reports).toEqual([
      ['a', 5],
      ['b', 2],
    ])
  })

  it('does not count time while the page is hidden', () => {
    const { clock, reports, wait } = setup()
    clock.show('a')
    wait(3000)
    clock.pause()
    wait(60_000)
    clock.resume()
    wait(1000)
    clock.pause()
    expect(reports).toEqual([
      ['a', 3],
      ['a', 1],
    ])
  })

  it('skips very short stays and repeated opens of the same task', () => {
    const { clock, reports, wait } = setup()
    clock.show('a')
    wait(200)
    clock.show('b')
    wait(1000)
    clock.show('b')
    wait(1000)
    clock.pause()
    expect(reports).toEqual([['b', 2]])
  })

  it('flushes the current stay before the finish', async () => {
    const { clock, reports, wait } = setup()
    clock.show('a')
    wait(4000)
    await clock.flush()
    await clock.flush()
    expect(reports).toEqual([['a', 4]])
  })
})
