import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { sessionStore } from '@/entities/session'
import { mockFetch, renderApp } from './test-utils'

const candidateSession = {
  accessToken: 't',
  user: {
    id: 'u1',
    email: 'dev@fsp.ru',
    role: 'candidate' as const,
    isEmailVerified: true,
    createdAt: '2026-01-01T00:00:00Z',
  },
}

describe('application routing', () => {
  afterEach(() => sessionStore.clear())

  it('renders the landing with the signup panel', async () => {
    renderApp('/')
    expect(await screen.findByRole('heading', { level: 1, name: 'КАДРЫ' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Я специалист' })).toBeInTheDocument()
  })

  it('validates email and routes the specialist to candidate registration', async () => {
    const { router } = renderApp('/')
    const user = userEvent.setup()

    await user.click(await screen.findByRole('button', { name: 'Я специалист' }))
    expect(screen.getByRole('alert')).toHaveTextContent('Укажите email')

    await user.type(screen.getByLabelText('Электронная почта'), 'dev@fsp.ru')
    await user.click(screen.getByRole('button', { name: 'Я специалист' }))

    await waitFor(() => expect(router.state.location.pathname).toBe('/auth/candidate'))
    expect(router.state.location.search).toContain('email=dev%40fsp.ru')
  })

  it('redirects guests from protected routes to auth', async () => {
    const { router } = renderApp('/profile')
    await waitFor(() => expect(router.state.location.pathname).toBe('/auth'))
    expect(router.state.location.search).toBe('?redirect=%2Fprofile')
  })

  it('blocks routes not allowed for the role', async () => {
    sessionStore.set(candidateSession)
    renderApp('/matching')
    expect(await screen.findByText('Нет доступа')).toBeInTheDocument()
  })

  it('shows a friendly state when the backend endpoint is not implemented yet', async () => {
    vi.stubGlobal(
      'fetch',
      mockFetch({
        '/api/v1/vacancies': {
          status: 501,
          body: { error: { code: 'not_implemented', message: 'vacancies.list' } },
        },
      }),
    )
    renderApp('/vacancies')
    expect(await screen.findByText('Раздел ещё в разработке.')).toBeInTheDocument()
  })

  it('renders not found for unknown URLs', async () => {
    renderApp('/definitely/missing')
    expect(await screen.findByRole('heading', { name: 'Страница не найдена' })).toBeInTheDocument()
  })
})
