import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { sessionStore } from '@/entities/session'
import { mockFetch, renderApp } from './test-utils'

const SLOW = { timeout: 5000 }

function signIn(role: 'candidate' | 'employer', name?: { firstName: string; lastName: string }) {
  sessionStore.set({
    accessToken: 't',
    user: {
      id: 'u1',
      email: 'dev@fsp.ru',
      role,
      isEmailVerified: true,
      createdAt: '2026-01-01T00:00:00Z',
      ...name,
    },
  })
}

const NO_COMPANY = {
  '/api/v1/companies/me': {
    status: 404,
    body: { error: { code: 'not_found', message: 'Профиль компании ещё не заполнен' } },
  },
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

    const manual = screen.getByRole('button', { name: 'Заполнить вручную' })
    expect(manual).toBeDisabled()
    await user.click(screen.getByLabelText(/обработку персональных данных/))
    await user.click(screen.getByLabelText(/работодатели увидят профиль/))
    await user.click(screen.getByLabelText('Да'))
    expect(screen.getByText(/привяжите ФСП ID в настройках/)).toBeInTheDocument()
    expect(screen.queryByLabelText(/ID участника/)).not.toBeInTheDocument()
    await user.click(screen.getByLabelText('Позже'))
    expect(manual).toBeEnabled()

    await user.click(manual)
    expect(screen.getByLabelText('Имя и фамилия')).toBeInTheDocument()
    expect(screen.getByLabelText('Нет опыта')).toBeInTheDocument()
    expect(screen.getByText('на руки, в месяц')).toBeInTheDocument()
  })

  it('asks an employer about themselves before the company', async () => {
    signIn('employer')
    vi.stubGlobal('fetch', mockFetch(NO_COMPANY))
    const { router } = renderApp('/feed/swipe')
    await waitFor(() => expect(router.state.location.pathname).toBe('/profile/company'), SLOW)
    expect(await screen.findByLabelText('Имя', {}, SLOW)).toBeInTheDocument()
    expect(screen.getByLabelText('Фамилия')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Настройка компании' })).toBeInTheDocument()
    expect(screen.getByText(/остальные разделы закрыты/)).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Свайпы' })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Далее' })).toBeInTheDocument()
  })

  it('checks the INN before the company profile step', async () => {
    signIn('employer', { firstName: 'Анна', lastName: 'Петрова' })
    vi.stubGlobal('fetch', mockFetch(NO_COMPANY))
    renderApp('/profile/company')
    const user = userEvent.setup()

    const inn = await screen.findByLabelText('ИНН', {}, SLOW)
    expect(screen.getByText(/Автозаполнение по ИНН — в разработке/)).toBeInTheDocument()
    await user.type(inn, '1234567890')
    await user.click(screen.getByRole('button', { name: 'Далее' }))
    expect(await screen.findByText(/ИНН/, { selector: '.field__error' })).toBeInTheDocument()

    await user.clear(inn)
    await user.type(inn, '7707083893')
    await user.click(screen.getByRole('button', { name: 'Далее' }))
    expect(await screen.findByLabelText('Название для кандидатов', {}, SLOW)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Сохранить и продолжить' })).toBeInTheDocument()
  })
})
