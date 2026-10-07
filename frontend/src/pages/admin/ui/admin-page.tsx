import type { ComponentType } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router'
import { adminQueries } from '../api/admin-api'
import { BankSection } from './bank/bank-section'
import { BanlistSection } from './banlist/banlist-section'
import { EmployersSection } from './employers/employers-section'
import { PlatformSection } from './platform/platform-section'
import { SettingsSection } from './settings/settings-section'
import { TaskAnalyticsSection } from './task-analytics/task-analytics-section'
import { TestsSection } from './tests/tests-section'
import { UsersSection } from './users/users-section'
import { VerificationSection } from './verification/verification-section'
import './admin.css'

type Section = { id: string; label: string; Component: ComponentType }

const SECTIONS: Section[] = [
  { id: 'bank', label: 'Банк заданий', Component: BankSection },
  { id: 'task-analytics', label: 'Аналитика заданий', Component: TaskAnalyticsSection },
  { id: 'platform', label: 'Продуктовая аналитика', Component: PlatformSection },
  { id: 'employers', label: 'Работодатели под подозрением', Component: EmployersSection },
  { id: 'banlist', label: 'Банлист', Component: BanlistSection },
  { id: 'settings', label: 'Справочники и параметры', Component: SettingsSection },
  { id: 'verification', label: 'Проверка компаний', Component: VerificationSection },
  { id: 'tests', label: 'Шаблоны тестов', Component: TestsSection },
  { id: 'users', label: 'Пользователи', Component: UsersSection },
]

/** The admin panel: one route, sections switch by `?tab=` (links to them can be shared). */
export function AdminPage() {
  const [params, setParams] = useSearchParams()
  const pending = useQuery(adminQueries.pendingCount())
  const active = SECTIONS.find((section) => section.id === params.get('tab')) ?? SECTIONS[0]!
  const { Component } = active

  return (
    <div className="admin">
      <nav className="admin__nav" aria-label="Разделы админки">
        <p className="admin__brand">Администрирование</p>
        <ul>
          {SECTIONS.map((section) => (
            <li key={section.id}>
              <button
                type="button"
                className="admin__link"
                aria-current={section.id === active.id ? 'page' : undefined}
                onClick={() => setParams({ tab: section.id })}
              >
                {section.label}
                {section.id === 'verification' && (pending.data ?? 0) > 0 && (
                  <span className="admin__badge" aria-label={`${pending.data} на проверке`}>
                    {pending.data}
                  </span>
                )}
              </button>
            </li>
          ))}
        </ul>
      </nav>
      <div className="admin__main">
        <Component key={active.id} />
      </div>
    </div>
  )
}
