import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, test, vi } from 'vitest'
import { sessionApi } from '@/entities/session'
import type * as sessionModule from '@/entities/session'
import { AuthForm } from '@/features/auth-by-email'
import { resumeValuesFrom } from '@/features/edit-resume/model/schema'

vi.mock('@/entities/session', async () => {
  const actual = await vi.importActual<typeof sessionModule>('@/entities/session')
  return {
    ...actual,
    sessionApi: {
      ...actual.sessionApi,
      yandexStatus: vi.fn<() => ReturnType<typeof actual.sessionApi.yandexStatus>>(),
      yandexStart: vi.fn<typeof actual.sessionApi.yandexStart>(),
    },
  }
})

function renderForm(mode: 'sign-in' | 'sign-up' = 'sign-in') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <AuthForm role="candidate" initialMode={mode} onSuccess={() => {}} />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.mocked(sessionApi.yandexStatus).mockReset()
  vi.mocked(sessionApi.yandexStart).mockReset()
})

test('the Yandex button stays hidden when the app is not configured', async () => {
  vi.mocked(sessionApi.yandexStatus).mockRejectedValue(new Error('missing'))
  renderForm()
  expect(await screen.findByRole('button', { name: 'Вход' })).toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'Войти через Яндекс' })).not.toBeInTheDocument()
})

test('sign-up does not leave for Yandex until the terms are accepted', async () => {
  vi.mocked(sessionApi.yandexStatus).mockResolvedValue({ enabled: true })
  const user = userEvent.setup()
  renderForm('sign-up')
  await user.click(await screen.findByRole('button', { name: 'Войти через Яндекс' }))
  expect(sessionApi.yandexStart).not.toHaveBeenCalled()
  expect(
    screen.getByText('Нужно принять Политику конфиденциальности и Пользовательское соглашение'),
  ).toBeInTheDocument()
})

test('an empty resume takes the name from the account', () => {
  expect(resumeValuesFrom(null, 'Анна Смирнова').displayName).toBe('Анна Смирнова')
  expect(resumeValuesFrom(null).displayName).toBe('')
})
