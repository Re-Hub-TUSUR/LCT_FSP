import { env, isAdminHost } from '../config'

/** Error envelope returned by the backend: `{ "error": { code, message, details } }`. */
type ErrorEnvelope = {
  error?: { code?: string; message?: string; details?: unknown }
}

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly details: unknown

  constructor(status: number, code: string, message: string, details?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.details = details
  }
}

type BanNotice = { reason: string; supportEmail: string }

type HttpHooks = {
  getAccessToken: () => string | null
  onUnauthorized: () => void
  /** 403 account_banned: the app replaces itself with the ban screen. */
  onBanned?: (notice: BanNotice) => void
  /** Returns a new access token, or null when the session cannot be restored. */
  refresh?: () => Promise<string | null>
}

// shared must not know about the session entity, so app/ injects these hooks at startup.
const hooks: HttpHooks = {
  getAccessToken: () => null,
  onUnauthorized: () => {},
}

export function configureHttp(next: Partial<HttpHooks>) {
  Object.assign(hooks, next)
}

type QueryValue = string | number | boolean | null | undefined | readonly (string | number)[]

export type RequestOptions = {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  body?: unknown
  query?: Record<string, QueryValue>
  signal?: AbortSignal
  headers?: Record<string, string>
  /** The refresh call itself must not trigger another refresh. */
  skipAuthRefresh?: boolean
}

/** Marks our fetch calls so a foreign form cannot reuse the refresh cookie. */
const CSRF_HEADER = { 'X-Kadry-Request': '1' }

/**
 * On the admin subdomain nginx already uses Authorization for the browser password.
 * The JWT travels in a side header, and that nginx copies it back to Authorization.
 */
export function accessHeaders(token: string | null): Record<string, string> {
  if (!token) return {}
  const value = `Bearer ${token}`
  return isAdminHost() ? { 'X-Kadry-Access': value } : { Authorization: value }
}

function buildUrl(path: string, query?: RequestOptions['query']) {
  const url = `${env.apiUrl}${path.startsWith('/') ? path : `/${path}`}`
  if (!query) return url

  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(query)) {
    if (value === undefined || value === null || value === '') continue
    if (Array.isArray(value)) value.forEach((item) => params.append(key, String(item)))
    else params.set(key, String(value))
  }
  const search = params.toString()
  return search ? `${url}?${search}` : url
}

async function maybeRefresh(response: Response, options: RequestOptions): Promise<boolean> {
  if (response.ok || response.status !== 401 || options.skipAuthRefresh || !hooks.refresh) {
    return false
  }
  return (await hooks.refresh()) !== null
}

function noticeBanned(error: ApiError) {
  if (error.code !== 'account_banned') return
  const details = (error.details ?? {}) as { reason?: unknown; supportEmail?: unknown }
  hooks.onBanned?.({
    reason: typeof details.reason === 'string' ? details.reason : error.message,
    supportEmail: typeof details.supportEmail === 'string' ? details.supportEmail : '',
  })
}

function errorFrom(response: Response, payload: unknown): ApiError {
  const envelope = (typeof payload === 'object' && payload !== null ? payload : {}) as ErrorEnvelope
  return new ApiError(
    response.status,
    envelope.error?.code ?? 'http_error',
    envelope.error?.message ?? response.statusText ?? 'Request failed',
    envelope.error?.details,
  )
}

async function parseBody(response: Response): Promise<unknown> {
  if (response.status === 204) return undefined
  const type = response.headers.get('content-type') ?? ''
  if (type.includes('application/json')) return response.json()
  const text = await response.text()
  return text || undefined
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, query, signal, headers = {} } = options
  const token = hooks.getAccessToken()
  const isForm = typeof FormData !== 'undefined' && body instanceof FormData

  let response: Response
  try {
    response = await fetch(buildUrl(path, query), {
      method,
      signal,
      credentials: 'include',
      headers: {
        Accept: 'application/json',
        ...CSRF_HEADER,
        ...(body !== undefined && !isForm && { 'Content-Type': 'application/json' }),
        ...accessHeaders(token),
        ...headers,
      },
      body: body === undefined ? undefined : isForm ? body : JSON.stringify(body),
    })
  } catch (cause) {
    if (cause instanceof DOMException && cause.name === 'AbortError') throw cause
    throw new ApiError(0, 'network_error', 'Сервер недоступен. Проверьте подключение.', cause)
  }

  const payload = await parseBody(response)

  if (!response.ok) {
    if (await maybeRefresh(response, options)) {
      return request<T>(path, { ...options, skipAuthRefresh: true })
    }
    const error = errorFrom(response, payload)
    if (response.status === 401) hooks.onUnauthorized()
    noticeBanned(error)
    throw error
  }

  return payload as T
}

export async function requestBlob(path: string, options: RequestOptions = {}): Promise<Blob> {
  const { query, signal, headers = {} } = options
  const token = hooks.getAccessToken()
  let response: Response
  try {
    response = await fetch(buildUrl(path, query), {
      method: 'GET',
      signal,
      credentials: 'include',
      headers: { ...CSRF_HEADER, ...accessHeaders(token), ...headers },
    })
  } catch (cause) {
    if (cause instanceof DOMException && cause.name === 'AbortError') throw cause
    throw new ApiError(0, 'network_error', 'Сервер недоступен. Проверьте подключение.', cause)
  }
  if (!response.ok) {
    if (await maybeRefresh(response, options)) {
      return requestBlob(path, { ...options, skipAuthRefresh: true })
    }
    const error = errorFrom(response, await parseBody(response))
    if (response.status === 401) hooks.onUnauthorized()
    noticeBanned(error)
    throw error
  }
  return response.blob()
}

export const http = {
  get: <T>(path: string, options?: Omit<RequestOptions, 'method' | 'body'>) =>
    request<T>(path, { ...options, method: 'GET' }),
  post: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, 'method' | 'body'>) =>
    request<T>(path, { ...options, method: 'POST', body }),
  put: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, 'method' | 'body'>) =>
    request<T>(path, { ...options, method: 'PUT', body }),
  patch: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, 'method' | 'body'>) =>
    request<T>(path, { ...options, method: 'PATCH', body }),
  delete: <T>(path: string, options?: Omit<RequestOptions, 'method' | 'body'>) =>
    request<T>(path, { ...options, method: 'DELETE' }),
  blob: (path: string, options?: Omit<RequestOptions, 'method' | 'body'>) =>
    requestBlob(path, options),
}
