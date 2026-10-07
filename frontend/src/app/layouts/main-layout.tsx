import { Outlet } from 'react-router'
import { useSession } from '@/entities/session'
import type { UserRole } from '@/entities/user'
import { ROUTES } from '@/shared/config'
import { NotificationToasts } from '@/features/notification-stream'
import { SiteHeader } from '@/widgets/site-header'
import type { NavItem } from '@/widgets/site-header'
import { CabinetGate, useCabinetSetup } from '../router/cabinet-gate'

const NAV_BY_ROLE: Record<UserRole | 'guest', NavItem[]> = {
  guest: [{ label: 'Вакансии', to: ROUTES.vacancies }],
  candidate: [
    { label: 'Свайпы', to: ROUTES.feedSwipe },
    { label: 'Лента', to: ROUTES.feed },
    { label: 'Мои отклики', to: ROUTES.responses },
    { label: 'Тестирование', to: ROUTES.testing },
    { label: 'Календарь', to: ROUTES.calendar },
  ],
  employer: [
    { label: 'Свайпы', to: ROUTES.feedSwipe },
    { label: 'Лента', to: ROUTES.feed },
    { label: 'Мои отклики', to: ROUTES.responses },
    { label: 'Вакансии', to: ROUTES.vacancies },
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
  const links = setup.phase === 'open' ? NAV_BY_ROLE[user?.role ?? 'guest'] : []
  const cta = !user
    ? { label: 'Войти', to: ROUTES.auth }
    : setup.phase === 'required'
      ? undefined
      : { label: 'Кабинет', to: ROUTES.profile }

  return (
    <>
      <div className="app-glow" aria-hidden="true" />
      <SiteHeader
        links={links}
        cta={cta}
        home={setup.phase === 'required' ? setup.setupPath : undefined}
      />
      <NotificationToasts />
      <main>
        <CabinetGate>
          <Outlet />
        </CabinetGate>
      </main>
    </>
  )
}
