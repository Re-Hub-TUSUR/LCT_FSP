import { useSession } from '@/entities/session'
import { ROUTES } from '@/shared/config'
import { LandingHero } from '@/widgets/landing-hero'
import { SiteHeader } from '@/widgets/site-header'
import type { NavItem } from '@/widgets/site-header'

const LANDING_LINKS: NavItem[] = [
  { label: 'Специалистам', to: '#specialists' },
  { label: 'Компаниям', to: '#companies' },
  { label: 'О платформе', to: '#about' },
  { label: 'Контакты', to: '#contacts' },
]

export function LandingPage() {
  const { user } = useSession()
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
