import { Link, NavLink, Outlet } from 'react-router'
import { useCandidatePhoto } from '@/entities/candidate'
import { companyLogoUrl } from '@/entities/company'
import { ROUTES } from '@/shared/config'
import { VerifiedMark } from '@/shared/ui'
import { initialsOf, isWaiting, useCabinetData, useCategoryLabel } from '../lib/cabinet-data'
import { Icon } from './cabinet-icons'
import type { CabinetIcon } from './cabinet-icons'
import './cabinet.css'

type NavEntry = { label: string; to: string; icon: CabinetIcon; count?: number }

export function CabinetLayout() {
  const { user, role, profile, company, invitations } = useCabinetData()
  const category = useCategoryLabel()
  // The query cache outlives a change of account: read only the current role's data.
  const candidate = role === 'candidate' ? profile.data : undefined
  const own = role === 'employer' ? company.data : undefined
  const photo = useCandidatePhoto(candidate?.id ?? null, candidate?.hasPhoto === true)

  const ready =
    role === 'admin' ||
    (role === 'candidate' && profile.isSuccess) ||
    (role === 'employer' && company.isSuccess)

  const items = invitations.data?.items ?? []
  const fresh =
    role === 'employer'
      ? items.filter(isWaiting).length
      : items.filter((item) => item.status === 'sent').length

  const links: NavEntry[] = !ready
    ? []
    : role === 'employer'
      ? [
          { label: 'Обзор', to: ROUTES.profile, icon: 'home' },
          { label: 'Приглашения', to: ROUTES.profileInvitations, icon: 'inbox', count: fresh },
          { label: 'Компания', to: ROUTES.profileCompany, icon: 'company' },
          { label: 'Настройки', to: ROUTES.profileSettings, icon: 'sliders' },
        ]
      : role === 'candidate'
        ? [
            { label: 'Обзор', to: ROUTES.profile, icon: 'home' },
            { label: 'Приглашения', to: ROUTES.profileInvitations, icon: 'inbox', count: fresh },
            { label: 'Профиль и резюме', to: ROUTES.profileResume, icon: 'user' },
            { label: 'Категория и грейд', to: ROUTES.profileCategory, icon: 'badge' },
            { label: 'Настройки', to: ROUTES.profileSettings, icon: 'sliders' },
          ]
        : []

  if (links.length === 0) {
    return (
      <div className="cabinet cabinet--setup">
        <div className="cabinet__main">
          <Outlet />
        </div>
      </div>
    )
  }

  const name = candidate?.displayName ?? own?.name ?? user?.email ?? ''
  const subtitle =
    role === 'candidate'
      ? (category ?? 'Категория после теста')
      : (own?.industry ?? 'Профиль компании')

  return (
    <div className="cabinet">
      <aside className="cabinet-side" aria-label="Меню кабинета">
        <div className="cabinet-me">
          <span className="cabinet-avatar" aria-hidden="true">
            {photo.data ? (
              <img src={photo.data} alt="" />
            ) : own?.hasLogo ? (
              <img src={companyLogoUrl(own.id)} alt="" />
            ) : (
              initialsOf(name)
            )}
          </span>
          <div className="cabinet-me__text">
            <p className="cabinet-me__name">
              {name}
              {own?.itAccredited && <VerifiedMark interactive={false} />}
            </p>
            <p className="cabinet-me__sub">{subtitle}</p>
          </div>
        </div>

        <nav className="cabinet-nav" aria-label="Разделы кабинета">
          {links.map((link) => (
            <NavLink key={link.to} to={link.to} end className="cabinet-nav__link">
              <Icon name={link.icon} />
              <span>{link.label}</span>
              {link.count ? (
                <span className="cabinet-nav__count">
                  {link.count}
                  <span className="visually-hidden"> новых</span>
                </span>
              ) : null}
            </NavLink>
          ))}
        </nav>

        {candidate && (
          <div className="cabinet-foot">
            <p className="cabinet-foot__title">
              <span
                className={
                  candidate.jobStatus === 'not_looking' ? 'cabinet-dot is-off' : 'cabinet-dot'
                }
                aria-hidden="true"
              />
              {candidate.jobStatus === 'not_looking' ? 'Профиль скрыт' : 'Профиль виден'}
            </p>
            <p>
              {candidate.jobStatus === 'not_looking'
                ? 'Новые работодатели вас не найдут'
                : 'Работодатели находят вас в подборке'}
            </p>
            <Link className="cabinet-foot__link" to={ROUTES.profileSettings}>
              {candidate.jobStatus === 'not_looking' ? 'Включить' : 'Настроить'}
            </Link>
          </div>
        )}
        {own && (
          <div className="cabinet-foot">
            <p className="cabinet-foot__title">
              <span
                className={own.itAccredited ? 'cabinet-dot' : 'cabinet-dot is-off'}
                aria-hidden="true"
              />
              {own.itAccredited
                ? 'IT-аккредитация подтверждена'
                : 'IT-аккредитация не подтверждена'}
            </p>
            <p>
              {own.itAccredited
                ? 'Кандидаты видят галочку рядом с названием'
                : 'Загрузите выписку Минцифры — появится галочка'}
            </p>
            <Link className="cabinet-foot__link" to={ROUTES.profileCompany}>
              {own.itAccredited ? 'Профиль компании' : 'Загрузить выписку'}
            </Link>
          </div>
        )}
      </aside>
      <div className="cabinet__main">
        <Outlet />
      </div>
    </div>
  )
}
