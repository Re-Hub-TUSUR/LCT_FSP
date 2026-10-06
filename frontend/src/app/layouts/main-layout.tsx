import { Outlet } from 'react-router'
import { useSession } from '@/entities/session'
import type { UserRole } from '@/entities/user'
import { ROUTES } from '@/shared/config'
import { SiteHeader } from '@/widgets/site-header'
import type { NavItem } from '@/widgets/site-header'

const NAV_BY_ROLE: Record<UserRole | 'guest', NavItem[]> = {
  guest: [{ label: 'Вакансии', to: ROUTES.vacancies }],
  candidate: [
    { label: 'Лента', to: ROUTES.feed },
    { label: 'Тестирование', to: ROUTES.testing },
    { label: 'Календарь', to: ROUTES.calendar },
  ],
  employer: [
    { label: 'Кандидаты', to: ROUTES.feed },
    { label: 'Вакансии', to: ROUTES.vacancies },
    { label: 'Календарь', to: ROUTES.calendar },
  ],
  admin: [
    { label: 'Админка', to: ROUTES.admin },
    { label: 'Вакансии', to: ROUTES.vacancies },
  ],
}

export function MainLayout() {
  const { user } = useSession()
  const links = NAV_BY_ROLE[user?.role ?? 'guest']
  const cta = user ? { label: 'Кабинет', to: ROUTES.profile } : { label: 'Войти', to: ROUTES.auth }

  return (
    <>
      <div className="app-glow" aria-hidden="true" />
      <SiteHeader links={links} cta={cta} />
      <main>
        <Outlet />
      </main>
    </>
  )
}
