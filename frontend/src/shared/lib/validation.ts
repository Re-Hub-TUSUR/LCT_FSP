import { z } from 'zod'

export const emailSchema = z.email()

export function isEmail(value: string): boolean {
  return emailSchema.safeParse(value).success
}

/** Accepts only same-origin app paths; `//host` and `/\host` are protocol-relative in browsers. */
export function isSafeInternalPath(value: string | null | undefined): value is string {
  return Boolean(
    value && value.startsWith('/') && !value.startsWith('//') && !value.startsWith('/\\'),
  )
}

/** Guards user-provided links against `javascript:` and other non-web schemes. */
export function isHttpUrl(value: string): boolean {
  try {
    const { protocol } = new URL(value)
    return protocol === 'http:' || protocol === 'https:'
  } catch {
    return false
  }
}
