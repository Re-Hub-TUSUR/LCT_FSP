import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { OwnCandidateDto } from '@/entities/candidate'
import type { CompanyDto } from '@/entities/company'
import type { InvitationDto } from '@/entities/invitation'
import { sessionStore } from '@/entities/session'
import { CompanyPanels } from '@/features/edit-company'
import { ResumePanels } from '@/features/edit-resume'
import { InvitationsBoard } from '@/widgets/invitations-inbox'
import { renderWithProviders, stubApi } from './test-utils'

const SLOW = { timeout: 5000 }

const DICTIONARY = {
  specializations: [{ code: 'backend', label: 'Backend-разработка' }],
  grades: [],
}

const PROFILE: OwnCandidateDto = {
  id: 'me',
  displayName: 'Анна Петрова',
  headline: 'Backend-разработчик',
  about: null,
  category: null,
  gradeVerified: false,
  assessmentScore: null,
  assessmentStatus: 'not_taken',
  stack: ['Python', 'FastAPI', 'PostgreSQL'],
  softSkills: [],
  experienceYears: 3,
  englishLevel: null,
  city: 'Казань',
  relocationReady: false,
  workFormats: ['remote'],
  salaryExpectation: 200000,
  fspAchievements: [],
  fspTitles: [],
  fspLinked: false,
  resumes: [],
  hasPhoto: false,
  contacts: { email: 'anna@example.com', phone: '+7 900 000-00-00', telegram: null },
  jobStatus: 'open',
  employmentTypes: ['full'],
  experienceEntries: [],
  noExperience: false,
  education: [],
  githubUrl: null,
  isMinor: false,
  lastActiveAt: null,
  searching: true,
  fspMemberId: null,
  specialization: 'backend',
  birthDate: null,
  profileDisplayConsent: true,
  fspSync: 'later',
}

const COMPANY: CompanyDto = {
  id: 'co',
  name: 'Технологии',
  industry: 'Финтех',
  description: 'Делаем платёжные сервисы для банков и магазинов. '.repeat(3),
  city: 'Москва',
  size: '51-200',
  website: 'https://tech.example',
  contactEmail: 'hr@tech.example',
  inn: '7707083893',
  ogrn: null,
  kpp: null,
  legalAddress: null,
  hasLogo: false,
  itAccredited: false,
}

function invitation(id: string, status: InvitationDto['status'], name: string): InvitationDto {
  return {
    id,
    candidateId: 'me',
    company: { id: `c-${id}`, name },
    vacancyId: null,
    message: `Приглашение от ${name}`,
    salary: { from: 200000, to: 250000 },
    contactMethod: 'Telegram',
    status,
    createdAt: '2026-10-01T10:00:00Z',
    updatedAt: '2026-10-02T10:00:00Z',
  }
}

function signIn(role: 'candidate' | 'employer') {
  sessionStore.set({
    accessToken: 't',
    user: {
      id: 'u1',
      email: 'anna@example.com',
      role,
      isEmailVerified: true,
      createdAt: '2026-01-01T00:00:00Z',
    },
  })
}

describe('cabinet panels', () => {
  afterEach(() => {
    sessionStore.clear()
    vi.unstubAllGlobals()
  })

  it('saves one resume panel with only its own fields', async () => {
    signIn('candidate')
    const calls = stubApi((call) => {
      if (call.path === '/categories/dictionary') return DICTIONARY
      if (call.method === 'PATCH') return { ...PROFILE, about: 'Пишу сервисы на Python' }
      return PROFILE
    })
    renderWithProviders(<ResumePanels profile={PROFILE} />)
    const user = userEvent.setup()

    const about = screen.getByRole('region', { name: 'О себе' })
    await user.click(within(about).getByRole('button', { name: 'Изменить' }))
    expect(screen.queryByRole('button', { name: 'Изменить' })).not.toBeInTheDocument()
    await user.type(within(about).getByLabelText('О себе'), 'Пишу сервисы на Python')
    await user.click(within(about).getByRole('button', { name: 'Сохранить' }))

    await waitFor(() => expect(calls.some((call) => call.method === 'PATCH')).toBe(true), SLOW)
    const patch = calls.find((call) => call.method === 'PATCH')
    expect(patch?.path).toBe('/candidates/me')
    expect(patch?.body).toEqual({ about: 'Пишу сервисы на Python' })
    expect(await screen.findByText('Сохранено.', {}, SLOW)).toBeInTheDocument()
  })

  it('keeps the e-mail read-only and the FSP results out of the form', () => {
    signIn('candidate')
    stubApi((call) => (call.path === '/categories/dictionary' ? DICTIONARY : PROFILE))
    renderWithProviders(<ResumePanels profile={PROFILE} />)

    const contacts = screen.getByRole('region', { name: 'Контакты' })
    expect(within(contacts).getByText('anna@example.com')).toBeInTheDocument()
    expect(within(contacts).getByText(/здесь не меняется/)).toBeInTheDocument()
    const fsp = screen.getByRole('region', { name: 'Достижения ФСП' })
    expect(within(fsp).queryByRole('button', { name: 'Изменить' })).not.toBeInTheDocument()
  })

  it('sends the whole company profile when one panel changes', async () => {
    signIn('employer')
    const calls = stubApi((call) =>
      call.method === 'PUT' ? { ...COMPANY, city: 'Казань' } : COMPANY,
    )
    renderWithProviders(<CompanyPanels company={COMPANY} />)
    const user = userEvent.setup()

    const profile = screen.getByRole('region', { name: 'Профиль для кандидатов' })
    await user.click(within(profile).getByRole('button', { name: 'Изменить' }))
    const city = within(profile).getByLabelText('Город')
    await user.clear(city)
    await user.type(city, 'Казань')
    await user.click(within(profile).getByRole('button', { name: 'Сохранить' }))

    await waitFor(() => expect(calls.some((call) => call.method === 'PUT')).toBe(true), SLOW)
    const put = calls.find((call) => call.method === 'PUT')
    expect(put?.path).toBe('/companies/me')
    expect(put?.body).toMatchObject({
      name: 'Технологии',
      city: 'Казань',
      inn: '7707083893',
      contactEmail: 'hr@tech.example',
    })
  })

  it('filters invitations and opens the chosen one from the URL', async () => {
    signIn('candidate')
    const items = [
      invitation('i1', 'sent', 'Альфа'),
      invitation('i2', 'accepted', 'Бета'),
      invitation('i3', 'declined', 'Гамма'),
    ]
    stubApi(() => ({ items, total: 3, page: 1, perPage: 20, pages: 1 }))
    const { router } = renderWithProviders(<InvitationsBoard direction="incoming" />, '/x?id=i2')
    const user = userEvent.setup()

    const detail = await screen.findByRole('article', { name: 'Приглашение' }, SLOW)
    expect(within(detail).getByText('Бета')).toBeInTheDocument()
    expect(within(detail).getByText(/работодатель видит ваши контакты/)).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /Новые/ }))
    expect(router.state.location.search).toBe('?status=sent')
    const list = screen.getByRole('list', { name: 'Приглашения' })
    expect(within(list).getAllByRole('button')).toHaveLength(1)
    expect(
      within(screen.getByRole('article', { name: 'Приглашение' })).getByText('Альфа'),
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Принять' })).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /Отклонённые/ }))
    await user.click(within(screen.getByRole('list', { name: 'Приглашения' })).getByRole('button'))
    expect(router.state.location.search).toBe('?status=declined&id=i3')
  })
})
