import { screen } from '@testing-library/react'
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

describe('legal documents', () => {
  afterEach(() => {
    sessionStore.clear()
    vi.unstubAllGlobals()
  })

  it.each([
    ['/privacy', 'Политика конфиденциальности', '/legal/kadry-privacy-policy.docx'],
    ['/terms', 'Пользовательское соглашение', '/legal/kadry-user-agreement.docx'],
    ['/consent', 'Согласие на обработку персональных данных', '/legal/kadry-consent.docx'],
  ])('opens %s for a guest with a contents list and a Word download', async (url, title, file) => {
    renderApp(url)

    expect(
      await screen.findByRole('heading', { level: 1, name: title }, { timeout: 5000 }),
    ).toBeInTheDocument()
    expect(screen.getByRole('navigation', { name: 'Содержание' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Скачать .docx' })).toHaveAttribute('href', file)
  })

  it('stays readable for a candidate who has no resume yet', async () => {
    sessionStore.set(candidateSession)
    vi.stubGlobal(
      'fetch',
      mockFetch({
        '/api/v1/candidates/me': { body: null },
      }),
    )

    const { router } = renderApp('/consent')

    expect(
      await screen.findByRole(
        'heading',
        { level: 1, name: 'Согласие на обработку персональных данных' },
        { timeout: 5000 },
      ),
    ).toBeInTheDocument()
    // The cabinet gate would have sent the candidate to the resume form.
    expect(router.state.location.pathname).toBe('/consent')
  })

  it('no longer prints the acceptance line on the landing', async () => {
    renderApp('/')

    await screen.findByRole('heading', { level: 1, name: 'КАДРЫ' }, { timeout: 5000 })
    expect(screen.queryByText(/Создавая аккаунт/)).not.toBeInTheDocument()
  })

  it('puts the acceptance line with both links on the registration checkbox', async () => {
    renderApp('/auth/candidate?mode=register')
    const user = userEvent.setup()

    const checkbox = await screen.findByRole(
      'checkbox',
      { name: /Создавая аккаунт, вы принимаете/ },
      { timeout: 5000 },
    )
    expect(screen.getAllByRole('checkbox')).toHaveLength(1)
    expect(screen.getByRole('link', { name: 'Политику конфиденциальности' })).toHaveAttribute(
      'href',
      '/privacy',
    )
    expect(screen.getByRole('link', { name: 'Пользовательское соглашение' })).toHaveAttribute(
      'href',
      '/terms',
    )
    for (const link of screen.getAllByRole('link', { name: /Политику|Пользовательское/ })) {
      expect(link).toHaveAttribute('target', '_blank')
    }

    // The box starts unticked: following a link never ticks it.
    expect(checkbox).not.toBeChecked()

    await user.type(screen.getByLabelText('Электронная почта'), 'dev@fsp.ru')
    await user.type(screen.getByLabelText('Пароль'), 'long-enough-password')
    await user.click(screen.getByRole('button', { name: 'Регистрация' }))
    const error = await screen.findByText(
      'Нужно принять Политику конфиденциальности и Пользовательское соглашение',
    )
    expect(error).toHaveAttribute('role', 'alert')
  })
})
