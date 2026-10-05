import type { ReactElement } from 'react'
import { QueryClient } from '@tanstack/react-query'
import { render } from '@testing-library/react'
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

/** Builds a `fetch` mock that answers JSON for matching paths and 404 otherwise. */
export function mockFetch(handlers: Record<string, { status?: number; body?: unknown }>) {
  return async (input: RequestInfo | URL) => {
    const url = new URL(typeof input === 'string' ? input : input.toString(), 'http://localhost')
    const match = handlers[url.pathname]
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
