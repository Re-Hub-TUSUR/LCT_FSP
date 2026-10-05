import { Link } from 'react-router'
import { ROUTES } from '@/shared/config'
import { Page } from '@/shared/ui'
import './auth-page.css'

/** Role choice: employers and candidates have different cabinets and registration paths. */
export function AuthPage() {
  return (
    <Page
      className="page--auth page--auth-wide"
      title="Вход в КАДРЫ"
      lead="Выберите, кто вы на платформе"
    >
      <div className="auth-choice">
        <Link className="auth-choice__item" to={ROUTES.candidateAuth}>
          <span className="auth-choice__title">Я специалист</span>
          <span className="auth-choice__text">
            Опрос, тест на грейд и приглашения от работодателей с зарплатой
          </span>
        </Link>
        <Link className="auth-choice__item" to={ROUTES.employerAuth}>
          <span className="auth-choice__title">Я ищу специалистов</span>
          <span className="auth-choice__text">
            Подборка кандидатов по категориям и прямые приглашения
          </span>
        </Link>
      </div>
    </Page>
  )
}
