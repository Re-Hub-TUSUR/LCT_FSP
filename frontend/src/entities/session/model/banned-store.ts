export type BanNotice = {
  reason: string
  supportEmail: string
}

type Listener = () => void

let current: BanNotice | null = null
const listeners = new Set<Listener>()

function emit() {
  listeners.forEach((listener) => listener())
}

/** In memory only. A reload after an unban shows the app again. */
export const bannedStore = {
  getSnapshot: (): BanNotice | null => current,
  subscribe(listener: Listener) {
    listeners.add(listener)
    return () => {
      listeners.delete(listener)
    }
  },
  set(next: BanNotice) {
    current = next
    emit()
  },
  clear() {
    if (current === null) return
    current = null
    emit()
  },
}
