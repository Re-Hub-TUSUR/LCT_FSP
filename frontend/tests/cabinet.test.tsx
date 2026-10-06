import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { sessionStore } from '@/entities/session'
import { mockFetch, renderApp } from './test-utils'

const SLOW = { timeout: 5000 }

function signIn(role: 'candidate' | 'employer') {
  sessionStore.set({
    accessToken: 't',
    user: {
      id: 'u1',
      email: 'dev@fsp.ru',
      role,
      isEmailVerified: true,
      createdAt: '2026-01-01T00:00:00Z',
    },
  })
}

describe('personal cabinet', () => {
  afterEach(() => {
    sessionStore.clear()
    vi.unstubAllGlobals()
  })

  it('starts a candidate without a resume on the first step', async () => {
    signIn('candidate')
    vi.stubGlobal(
      'fetch',
      mockFetch({
        '/api/v1/candidates/me': {
          status: 404,
          body: { error: { code: 'not_found', message: 'Сначала сохраните резюме' } },
        },
      }),
    )
    const { router } = renderApp('/feed/swipe')
    const user = userEvent.setup()

    await waitFor(() => expect(router.state.location.pathname).toBe('/profile/resume'), SLOW)
    expect(
      await screen.findByText(/Есть готовое резюме\? Приложите его/, {}, SLOW),
    ).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Свайпы' })).not.toBeInTheDocument()
    expect(screen.getByText(/остальные разделы закрыты/)).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Заполнить вручную' }))
    expect(screen.getByLabelText('Имя и фамилия')).toBeInTheDocument()
  })

  it('asks an employer to fill the company before anything else', async () => {
    signIn('employer')
    vi.stubGlobal(
      'fetch',
      mockFetch({
        '/api/v1/companies/me': {
          status: 404,
          body: { error: { code: 'not_found', message: 'Профиль компании ещё не заполнен' } },
        },
      }),
    )
    const { router } = renderApp('/feed/swipe')
    await waitFor(() => expect(router.state.location.pathname).toBe('/profile/company'), SLOW)
    expect(await screen.findByLabelText('Название', {}, SLOW)).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Профиль компании' })).toBeInTheDocument()
    expect(screen.getByText(/остальные разделы закрыты/)).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Свайпы' })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Сохранить' })).toBeInTheDocument()
  })
})
