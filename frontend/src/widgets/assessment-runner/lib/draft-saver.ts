type Options = {
  /** Save this long after the last change… */
  idleMs?: number
  /** …but never keep a change unsaved longer than this, however steadily the typing goes on. */
  maxWaitMs?: number
  onSaved?: () => void
  onFailed?: (error: unknown) => void
}

/**
 * Saves typed answers (code, free text) in the background.
 *
 * A pause in typing triggers a save, and so does `maxWaitMs` without any pause: somebody who
 * types non-stop until the time runs out must not lose everything since their last breath.
 */
export function createDraftSaver<T>(
  save: (id: string, value: T) => Promise<unknown>,
  { idleMs = 1000, maxWaitMs = 5000, onSaved, onFailed }: Options = {},
) {
  const pending = new Map<string, T>()
  let idle: ReturnType<typeof setTimeout> | undefined
  let limit: ReturnType<typeof setTimeout> | undefined

  /** Sends everything not saved yet; rejects when a save fails. */
  const flush = async () => {
    clearTimeout(idle)
    clearTimeout(limit)
    limit = undefined
    const batch = [...pending.entries()]
    pending.clear()
    await Promise.all(batch.map(([id, value]) => save(id, value)))
  }

  const saveInBackground = () => {
    flush().then(onSaved, onFailed)
  }

  return {
    /** Remembers the newest value of an answer and schedules its save. */
    change(id: string, value: T) {
      pending.set(id, value)
      clearTimeout(idle)
      idle = setTimeout(saveInBackground, idleMs)
      limit ??= setTimeout(saveInBackground, maxWaitMs)
    },
    flush,
  }
}
