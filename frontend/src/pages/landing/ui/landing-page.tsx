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

const LANDING_CTA: NavItem = { label: 'Войти', to: ROUTES.auth }

export function LandingPage() {
  return <LandingHero header={<SiteHeader links={LANDING_LINKS} cta={LANDING_CTA} overlay />} />
}
