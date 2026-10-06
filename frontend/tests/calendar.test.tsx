import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { CalendarEventDto } from '@/entities/calendar-event'
import { sessionStore } from '@/entities/session'
import type { UserRole } from '@/entities/user'
import { mockFetch, renderApp } from './test-utils'

// The first render loads the lazy page chunk, which can take longer than the default 1 s.
const SLOW = { timeout: 5000 }

function signIn(role: UserRole) {
  sessionStore.set({
    accessToken: 't',
    user: { id: 'u1', email: 'u@fsp.ru', role, isEmailVerified: true, createdAt: '2026-01-01' },
  })
}

// Noon of the current day is always inside the week the calendar opens on.
const noon = new Date()
noon.setHours(12, 0, 0, 0)

const meeting: CalendarEventDto = {
  id: 'm1',
  title: 'Техническое интервью',
  kind: 'interview',
  startsAt: noon.toISOString(),
  endsAt: new Date(noon.getTime() + 3_600_000).toISOString(),
  invitationId: null,
  status: 'pending',
  company: { id: 'c1', name: 'ПэйФлоу' },
  candidate: { id: 'p1', name: 'Марина Крылова' },
  vacancy: null,
  location: 'https://meet.example/1',
  note: null,
}

function stubFetch(handlers: Parameters<typeof mockFetch>[0]) {
  const fetchMock = vi.fn<typeof fetch>(mockFetch(handlers))
  vi.stubGlobal('fetch', fetchMock)
  return () => fetchMock.mock.calls.filter(([, init]) => init?.method === 'POST')
}

describe('calendar', () => {
  afterEach(() => sessionStore.clear())

  it('lets an employer schedule a meeting with a candidate found in the bank', async () => {
    signIn('employer')
    const posts = stubFetch({
      '/api/v1/calendar/events': { body: [meeting] },
      '/api/v1/vacancies/mine': { body: { items: [], total: 0, page: 1, perPage: 100, pages: 0 } },
      '/api/v1/candidates': {
        body: {
          items: [{ candidate: { id: 'p2', displayName: 'Илья Соколов', headline: 'Go' } }],
          total: 1,
          page: 1,
          perPage: 6,
          pages: 1,
          engine: 'database',
        },
      },
    })
    const user = userEvent.setup()

    renderApp('/calendar')
    expect(await screen.findByText('Марина Крылова', {}, SLOW)).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Назначить встречу' }))
    const dialog = await screen.findByRole('dialog', { name: 'Назначить встречу' })
    await user.click(await within(dialog).findByRole('button', { name: /Илья Соколов/ }))
    await user.click(within(dialog).getByRole('button', { name: 'Назначить' }))

    await waitFor(() => expect(posts()).toHaveLength(1))
    const [url, init] = posts()[0]!
    expect(url).toContain('/calendar/events')
    expect(JSON.parse(String(init?.body))).toMatchObject({
      candidateId: 'p2',
      title: 'Собеседование',
    })
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
  })

  it('lets a candidate confirm a meeting a company scheduled', async () => {
    signIn('candidate')
    const posts = stubFetch({
      '/api/v1/calendar/events': { body: [meeting] },
      '/api/v1/calendar/events/m1/confirm': { body: { ...meeting, status: 'confirmed' } },
    })
    const user = userEvent.setup()

    renderApp('/calendar')
    await user.click(await screen.findByRole('button', { name: /ПэйФлоу/ }, SLOW))

    const dialog = await screen.findByRole('dialog', { name: 'Техническое интервью' })
    expect(within(dialog).getByText('Ждёт ответа')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Назначить встречу' })).not.toBeInTheDocument()
    await user.click(within(dialog).getByRole('button', { name: 'Подтвердить' }))

    await waitFor(() => expect(posts()).toHaveLength(1))
    expect(posts()[0]![0]).toContain('/calendar/events/m1/confirm')
  })
})
