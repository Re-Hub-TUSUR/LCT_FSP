import { Link } from 'react-router'
import { BRAND, ROUTES } from '@/shared/config'
import { HackerRain, HackerText, Ornament, Page } from '@/shared/ui'
import './auth-page.css'

/** The sign of a role: a specialist writes code, a company holds a team. */
export function RoleGlyph({ role }: { role: 'candidate' | 'employer' }) {
  return role === 'candidate' ? (
    <span className="auth-glyph" aria-hidden="true">
      {'<'}
      <span className="auth-glyph__red">/</span>
      {'>'}
    </span>
  ) : (
    <span className="auth-glyph" aria-hidden="true">
      {'{'}
      <span className="auth-glyph__ink">•</span>
      {'}'}
    </span>
  )
}

export function PlatformChip() {
  return (
    <span className="auth-chip">
      <span>[</span> Платформа ФСП России <span>]</span>
    </span>
  )
}

/** Role choice: employers and candidates have different cabinets and registration paths. */
export function AuthPage() {
  return (
    <>
      <HackerRain />
      <Page
        className="page--auth page--auth-wide"
        eyebrow={<PlatformChip />}
        title={
          <>
            <HackerText text="Вход в " />
            <span className="auth-brand">
              <HackerText text={BRAND} />
            </span>
          </>
        }
        lead="Выберите, кто вы на платформе"
      >
        <div className="auth-choice">
          <Link className="auth-choice__item" to={ROUTES.candidateAuth}>
            <span className="auth-choice__top" aria-hidden="true">
              <RoleGlyph role="candidate" />
              <span className="auth-choice__arrow">→</span>
            </span>
            <span className="auth-choice__title">
              <HackerText text="Я специалист" />
            </span>
            <span className="auth-choice__text">
              Опрос, тест на грейд и приглашения от работодателей с зарплатой
            </span>
          </Link>
          <Link className="auth-choice__item" to={ROUTES.employerAuth}>
            <span className="auth-choice__top" aria-hidden="true">
              <RoleGlyph role="employer" />
              <span className="auth-choice__arrow">→</span>
            </span>
            <span className="auth-choice__title">
              <HackerText text="Я ищу специалистов" />
            </span>
            <span className="auth-choice__text">
              Подборка кандидатов по категориям и прямые приглашения
            </span>
          </Link>
        </div>
      </Page>
      <Ornament className="auth-strip" length={60} />
    </>
  )
}
