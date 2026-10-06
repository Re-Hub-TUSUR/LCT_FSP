import { useQuery } from '@tanstack/react-query'
import { NavLink, Outlet } from 'react-router'
import { candidateQueries } from '@/entities/candidate'
import { companyQueries } from '@/entities/company'
import { useSession } from '@/entities/session'
import { ROUTES } from '@/shared/config'
import './cabinet.css'

const CANDIDATE_LINKS = [
  { label: 'Приглашения', to: ROUTES.profile, end: true },
  { label: 'Резюме', to: ROUTES.profileResume, end: true },
  { label: 'Категория', to: ROUTES.profileCategory, end: true },
  { label: 'Настройки', to: ROUTES.profileSettings, end: true },
] as const

const EMPLOYER_LINKS = [
  { label: 'Кабинет', to: ROUTES.profile, end: true },
  { label: 'Компания', to: ROUTES.profileCompany, end: true },
  { label: 'Настройки', to: ROUTES.profileSettings, end: true },
] as const

export function CabinetLayout() {
  const { user } = useSession()
  const candidate = useQuery({
    ...candidateQueries.mine(),
    enabled: user?.role === 'candidate',
  })
  const company = useQuery({
    ...companyQueries.mine(),
    enabled: user?.role === 'employer',
  })
  const ready =
    user?.role === 'admin' ||
    (user?.role === 'candidate' && candidate.isSuccess) ||
    (user?.role === 'employer' && company.isSuccess)
  const links = !ready
    ? []
    : user?.role === 'employer'
      ? EMPLOYER_LINKS
      : user?.role === 'candidate'
        ? CANDIDATE_LINKS
        : []

  return (
    <div className={links.length > 0 ? 'cabinet' : 'cabinet cabinet--setup'}>
      {links.length > 0 && (
        <nav className="cabinet-nav" aria-label="Разделы кабинета">
          {links.map((link) => (
            <NavLink key={link.to} to={link.to} end={link.end} className="cabinet-nav__link">
              {link.label}
            </NavLink>
          ))}
        </nav>
      )}
      <div className="cabinet__main">
        <Outlet />
      </div>
    </div>
  )
}
