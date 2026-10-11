import { useState } from 'react'
import { NavLink, Outlet, useMatch } from 'react-router'
import { ROUTES } from '@/shared/config'
import { HackerRain } from '@/shared/ui'
import { useCabinetData, useCategoryLabel } from '../lib/cabinet-data'
import type { CabinetOutlet } from '../lib/cabinet-data'
import { CandidateHero, EmployerHero } from './cabinet-hero'
import './cabinet.css'

type NavEntry = { label: string; to: string }

export function CabinetLayout() {
  const { role, profile, company, invitations } = useCabinetData()
  const category = useCategoryLabel()
  const onOverview = useMatch({ path: ROUTES.profile, end: true }) !== null
  // The query cache outlives a change of account: read only the current role's data.
  const candidate = role === 'candidate' ? profile.data : undefined
  const own = role === 'employer' ? company.data : undefined

  const [settingUp, setSettingUp] = useState(false)
  const outlet: CabinetOutlet = { settingUp, setSettingUp }

  // `/me` answers null until the resume or the company is saved: an empty answer is still the
  // setup, without the sections. Leaving the setup layout also mounts the page anew, so the
  // employer's wizard keeps the setup until its last step is done.
  const ready =
    role === 'admin' ||
    (role === 'candidate' && Boolean(profile.data)) ||
    (role === 'employer' && Boolean(company.data) && !settingUp)

  const items = invitations.data?.items

  const links: NavEntry[] = !ready
    ? []
    : role === 'employer'
      ? [
          { label: 'Обзор', to: ROUTES.profile },
          { label: 'Компания', to: ROUTES.profileCompany },
          { label: 'Настройки', to: ROUTES.profileSettings },
        ]
      : role === 'candidate'
        ? [
            { label: 'Обзор', to: ROUTES.profile },
            { label: 'Профиль и резюме', to: ROUTES.profileResume },
            { label: 'Категория и грейд', to: ROUTES.profileCategory },
            { label: 'Настройки', to: ROUTES.profileSettings },
          ]
        : []

  if (links.length === 0) {
    return (
      <div className="cabinet cabinet--setup">
        <HackerRain />
        <div className="cabinet__main">
          <Outlet context={outlet} />
        </div>
      </div>
    )
  }

  return (
    <div className="cabinet">
      <HackerRain />
      {/* The blue plate opens the overview only; other sections start with their own title. */}
      {onOverview && own && <EmployerHero company={own} invitations={items} />}
      {onOverview && candidate && (
        <CandidateHero profile={candidate} category={category} invitations={items} />
      )}

      <nav className="cabinet-nav" aria-label="Разделы кабинета">
        {links.map((link) => (
          <NavLink key={link.to} to={link.to} end className="cabinet-nav__link">
            {link.label}
          </NavLink>
        ))}
      </nav>

      <div className="cabinet__main">
        <Outlet context={outlet} />
      </div>
    </div>
  )
}
