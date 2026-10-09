import { Navigate } from 'react-router'
import { useSession } from '@/entities/session'
import { isAdminHost, ROUTES } from '@/shared/config'
import { LandingHero } from '@/widgets/landing-hero'
import { SiteHeader } from '@/widgets/site-header'
import type { NavItem } from '@/widgets/site-header'

const LANDING_LINKS: NavItem[] = [
  { label: 'Специалистам', to: '#specialists' },
  { label: 'Компаниям', to: '#companies' },
  { label: 'Как проверяем', to: '#testing' },
  { label: 'Начать', to: '#start' },
]

export function LandingPage() {
  const { user } = useSession()
  if (isAdminHost()) return <Navigate to={ROUTES.admin} replace />
  const cta: NavItem = user
    ? { label: 'Кабинет', to: ROUTES.profile }
    : { label: 'Войти', to: ROUTES.auth }

  return (
    <>
      <SiteHeader links={LANDING_LINKS} cta={cta} overlay />
      <LandingHero />
    </>
  )
}
