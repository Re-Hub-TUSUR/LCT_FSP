import type { ReactElement } from 'react'
import { QueryClient } from '@tanstack/react-query'
import { render } from '@testing-library/react'
import { vi } from 'vitest'
import { createMemoryRouter, RouterProvider } from 'react-router'
import type { RouteObject } from 'react-router'
import { AppProviders } from '@/app/providers/app-providers'
import { routes } from '@/app/router/routes'

export function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
}

/** Renders the real application route tree at the given URL. */
export function renderApp(url = '/', appRoutes: RouteObject[] = routes) {
  const router = createMemoryRouter(appRoutes, { initialEntries: [url] })
  const utils = render(
    <AppProviders queryClient={createTestQueryClient()}>
      <RouterProvider router={router} />
    </AppProviders>,
  )
  return { ...utils, router }
}

/** Renders a single component inside a router and query client. */
export function renderWithProviders(ui: ReactElement, url = '/') {
  return renderApp(url, [{ path: '*', element: ui }])
}

/** A saved cabinet, so existing screens stay open unless a test overrides these paths. */
const filledCabinet: Record<string, { status?: number; body?: unknown }> = {
  '/api/v1/candidates/me': { body: { id: 'me' } },
  '/api/v1/companies/me': { body: { id: 'co', name: 'Компания' } },
}

/** Builds a `fetch` mock that answers JSON for matching paths and 404 otherwise. */
export function mockFetch(handlers: Record<string, { status?: number; body?: unknown }>) {
  return async (input: RequestInfo | URL) => {
    const url = new URL(typeof input === 'string' ? input : input.toString(), 'http://localhost')
    const match = Object.hasOwn(handlers, url.pathname)
      ? handlers[url.pathname]
      : filledCabinet[url.pathname]
    const status = match?.status ?? (match ? 200 : 404)
    return new Response(
      JSON.stringify(match?.body ?? { error: { code: 'not_found', message: 'Not found' } }),
      {
        status,
        headers: { 'Content-Type': 'application/json' },
      },
    )
  }
}

export type ApiCall = { method: string; path: string; body: unknown }

/** A `fetch` whose answers may depend on what was called before. */
export function stubApi(answer: (call: ApiCall, calls: ApiCall[]) => unknown) {
  const calls: ApiCall[] = []
  vi.stubGlobal('fetch', async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = new URL(typeof input === 'string' ? input : input.toString(), 'http://localhost')
    const call: ApiCall = {
      method: init?.method ?? 'GET',
      path: url.pathname.replace('/api/v1', ''),
      body: init?.body ? JSON.parse(String(init.body)) : undefined,
    }
    const body = answer(call, calls)
    calls.push(call)
    return new Response(body === undefined ? null : JSON.stringify(body), {
      status: body === undefined ? 204 : 200,
      headers: { 'Content-Type': 'application/json' },
    })
  })
  return calls
}
