import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, configureHttp, http } from './http'

const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

describe('http client', () => {
  afterEach(() => configureHttp({ getAccessToken: () => null, onUnauthorized: () => {} }))

  it('prefixes the API base URL, serialises query and attaches the bearer token', async () => {
    const fetchMock = vi.fn<typeof fetch>(async () => json(200, { ok: true }))
    vi.stubGlobal('fetch', fetchMock)
    configureHttp({ getAccessToken: () => 'token-1' })

    await expect(
      http.get('/vacancies', { query: { grade: 'middle', stack: ['go', 'sql'], search: '' } }),
    ).resolves.toEqual({ ok: true })

    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit]
    expect(url).toBe('/api/v1/vacancies?grade=middle&stack=go&stack=sql')
    expect((init.headers as Record<string, string>).Authorization).toBe('Bearer token-1')
  })

  it('maps the backend error envelope to ApiError', async () => {
    vi.stubGlobal('fetch', async () =>
      json(409, { error: { code: 'email_taken', message: 'Email уже занят' } }),
    )

    const error = await http.post('/auth/register', {}).catch((e: unknown) => e)
    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({ status: 409, code: 'email_taken', message: 'Email уже занят' })
  })

  it('notifies about 401 so the session can be cleared', async () => {
    const onUnauthorized = vi.fn<() => void>()
    configureHttp({ onUnauthorized })
    vi.stubGlobal('fetch', async () => json(401, { error: { code: 'unauthorized', message: 'x' } }))

    await expect(http.get('/users/me')).rejects.toBeInstanceOf(ApiError)
    expect(onUnauthorized).toHaveBeenCalledOnce()
  })

  it('reports network failures as status 0', async () => {
    vi.stubGlobal('fetch', async () => {
      throw new TypeError('Failed to fetch')
    })

    await expect(http.get('/health')).rejects.toMatchObject({ status: 0, code: 'network_error' })
  })
})
