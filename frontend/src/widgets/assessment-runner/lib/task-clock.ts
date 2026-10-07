type Report = (taskId: string, seconds: number) => Promise<unknown>

/** Shorter stays (a click through the task list) are not worth a request. */
const MIN_SECONDS = 0.5

/**
 * Measures how long each task is on screen. The time of a task is reported when the candidate
 * leaves it: another task, a hidden tab, the finish. The server sums the reports per task.
 */
export function createTaskClock(report: Report, now: () => number = () => performance.now()) {
  let current: string | null = null
  let since = 0
  let running = false

  const stop = (): Promise<unknown> => {
    if (!current || !running) return Promise.resolve()
    running = false
    const seconds = (now() - since) / 1000
    return seconds >= MIN_SECONDS ? report(current, seconds) : Promise.resolve()
  }

  return {
    /** The candidate opened a task: the previous one gets its time. */
    show(taskId: string) {
      if (taskId === current && running) return
      void stop().catch(() => {})
      current = taskId
      since = now()
      running = true
    },
    /** The page is hidden or the runner closes. */
    pause() {
      void stop().catch(() => {})
    },
    resume() {
      if (!current || running) return
      since = now()
      running = true
    },
    /** Reports the current stay and waits for it, e.g. right before the finish. */
    async flush() {
      await stop()
    },
  }
}
