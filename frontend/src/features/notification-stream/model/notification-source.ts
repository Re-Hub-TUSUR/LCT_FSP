import { refreshSession } from '@/entities/session'
import { accessHeaders } from '@/shared/api'
import { env } from '@/shared/config'
import type { NotificationEvent } from './use-notification-stream'

type Listener = (event: NotificationEvent) => void

const RETRY_MIN = 1_000
const RETRY_MAX = 30_000

const listeners = new Set<Listener>()
let connection: { token: string; controller: AbortController } | null = null

/**
 * One stream per tab, however many widgets listen: the toasts and the messenger share it.
 * Returns the unsubscribe; the stream closes with its last listener.
 */
export function subscribeToNotifications(token: string, listener: Listener): () => void {
  listeners.add(listener)
  if (connection?.token !== token) {
    connection?.controller.abort()
    const controller = new AbortController()
    connection = { token, controller }
    void run(token, controller.signal)
  }
  return () => {
    listeners.delete(listener)
    if (listeners.size === 0) {
      connection?.controller.abort()
      connection = null
    }
  }
}

function wait(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve) => {
    const timer = setTimeout(resolve, ms)
    signal.addEventListener(
      'abort',
      () => {
        clearTimeout(timer)
        resolve()
      },
      { once: true },
    )
  })
}

/** Keeps the stream open: a proxy timeout, a deploy or a sleeping laptop all end in a reconnect. */
async function run(token: string, signal: AbortSignal) {
  let delay = RETRY_MIN
  while (!signal.aborted) {
    try {
      const response = await fetch(`${env.apiUrl}/notifications/stream`, {
        headers: {
          Accept: 'text/event-stream',
          ...accessHeaders(token),
          'X-Kadry-Request': '1',
        },
        credentials: 'include',
        signal,
      })
      if (response.status === 401) {
        // A fresh token changes the session, and the listeners subscribe again with it.
        if ((await refreshSession()) !== null) return
      } else if (response.status >= 400 && response.status < 500) {
        // Any other client error will not fix itself on retry.
        return
      } else if (response.ok && response.body) {
        if (await read(response.body)) delay = RETRY_MIN
      }
    } catch {
      /* the network dropped or the stream was aborted: the loop decides which */
    }
    if (signal.aborted) return
    await wait(delay, signal)
    delay = Math.min(delay * 2, RETRY_MAX)
  }
}

/** Resolves when the server closes the stream; true when it delivered anything. */
async function read(body: ReadableStream<Uint8Array>): Promise<boolean> {
  const reader = body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let received = false
  while (true) {
    const { done, value } = await reader.read()
    if (done) return received
    received = true
    buffer += decoder.decode(value, { stream: true })
    const chunks = buffer.split('\n\n')
    buffer = chunks.pop() ?? ''
    for (const chunk of chunks) {
      const line = chunk.split('\n').find((row) => row.startsWith('data: '))
      if (!line) continue
      let payload: NotificationEvent
      try {
        payload = JSON.parse(line.slice(6)) as NotificationEvent
      } catch {
        continue
      }
      for (const listener of listeners) listener(payload)
    }
  }
}
