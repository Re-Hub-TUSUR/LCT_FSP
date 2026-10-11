import { Outlet } from 'react-router'
import { useSession } from '@/entities/session'
import type { UserRole } from '@/entities/user'
import { isAdminHost, ROUTES } from '@/shared/config'
import { NotificationToasts } from '@/features/notification-stream'
import { SiteHeader } from '@/widgets/site-header'
import type { NavItem } from '@/widgets/site-header'
import { CabinetGate, useCabinetSetup } from '../router/cabinet-gate'

const NAV_BY_ROLE: Record<UserRole | 'guest', NavItem[]> = {
  guest: [{ label: 'Вакансии', to: ROUTES.vacancies }],
  candidate: [
    { label: 'Лента', to: ROUTES.feed },
    { label: 'Свайпы', to: ROUTES.feedSwipe },
    { label: 'Мои отклики', to: ROUTES.responses },
    { label: 'Тестирование', to: ROUTES.testing },
    { label: 'Календарь', to: ROUTES.calendar },
  ],
  employer: [
    { label: 'Лента', to: ROUTES.feed },
    { label: 'Свайпы', to: ROUTES.feedSwipe },
    { label: 'Мои отклики', to: ROUTES.responses },
    { label: 'Вакансии', to: ROUTES.vacancies },
    { label: 'ATS', to: ROUTES.ats },
    { label: 'Тестовые', to: ROUTES.testing },
    { label: 'Календарь', to: ROUTES.calendar },
  ],
  admin: [
    { label: 'Админка', to: ROUTES.admin },
    { label: 'Вакансии', to: ROUTES.vacancies },
  ],
}

export function MainLayout() {
  const { user } = useSession()
  const setup = useCabinetSetup()
  const onAdminHost = isAdminHost()
  const links = setup.phase === 'open' ? NAV_BY_ROLE[user?.role ?? 'guest'] : []
  const cta = onAdminHost
    ? undefined
    : !user
      ? { label: 'Войти', to: ROUTES.auth }
      : setup.phase === 'required'
        ? undefined
        : { label: 'Кабинет', to: ROUTES.profile }

  const home = onAdminHost ? ROUTES.admin : setup.phase === 'required' ? setup.setupPath : undefined

  return (
    <>
      <div className="app-glow" aria-hidden="true" />
      <SiteHeader links={links} cta={cta} home={home} />
      <NotificationToasts />
      <main>
        <CabinetGate>
          <Outlet />
        </CabinetGate>
      </main>
    </>
  )
}
