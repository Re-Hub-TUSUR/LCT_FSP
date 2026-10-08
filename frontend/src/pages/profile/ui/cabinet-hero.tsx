import { Link } from 'react-router'
import type { OwnCandidateDto } from '@/entities/candidate'
import type { CompanyDto } from '@/entities/company'
import type { InvitationDto } from '@/entities/invitation'
import { ROUTES } from '@/shared/config'
import { isWaiting } from '../lib/cabinet-data'
import { candidateTodos } from '../lib/todos'

type EmployerProps = {
  company: CompanyDto
  /** Undefined while the list loads or when invitations are not available yet. */
  invitations: InvitationDto[] | undefined
}

/** Blue plate at the top of the company cabinet: the name, three numbers and the way to the bank. */
export function EmployerHero({ company, invitations }: EmployerProps) {
  const waiting = invitations?.filter(isWaiting).length ?? 0
  const accepted = invitations?.filter((item) => item.status === 'accepted').length
  const count = (value: number | undefined) => (invitations ? String(value ?? 0) : '—')
  const stats = [
    { label: 'Приглашений', value: count(invitations?.length) },
    { label: 'Ждут ответа', value: count(waiting) },
    { label: 'Приняли', value: count(accepted) },
  ]

  return (
    <section className="cabinet-hero" aria-labelledby="page-title">
      <span className="cabinet-hero__glyph" aria-hidden="true">
        {'{'}
        <span>•</span>
        {'}'}
      </span>
      <div className="cabinet-hero__main">
        <span className="cabinet-hero__kicker">Кабинет компании</span>
        <h1 id="page-title" className="cabinet-hero__title">
          {company.name}
          {company.itAccredited && (
            <span className="cabinet-hero__check" title="IT-аккредитация">
              ✓<span className="visually-hidden">IT-аккредитация подтверждена</span>
            </span>
          )}
        </h1>
        <p className="cabinet-hero__lead">
          {waiting > 0
            ? `Ждут ответа кандидатов: ${waiting}. Контакты откроются после согласия.`
            : 'Найдите кандидатов в банке и отправьте предложение с зарплатой.'}
        </p>
      </div>
      <div className="cabinet-hero__side">
        <dl className="cabinet-hero__stats">
          {stats.map((stat) => (
            <div key={stat.label}>
              <dd>{stat.value}</dd>
              <dt>{stat.label}</dt>
            </div>
          ))}
        </dl>
        <Link className="cabinet-hero__cta" to={ROUTES.feed}>
          Открыть банк кандидатов <span aria-hidden="true">→</span>
        </Link>
      </div>
    </section>
  )
}

type CandidateProps = {
  profile: OwnCandidateDto
  /** «Backend-разработка · Middle», or null before the test. */
  category: string | null
  invitations: InvitationDto[] | undefined
}

/** Blue plate at the top of the specialist's cabinet: the name and how complete the profile is. */
export function CandidateHero({ profile, category, invitations }: CandidateProps) {
  const firstName = profile.displayName.split(/\s+/)[0] || profile.displayName
  const fresh = invitations?.filter((item) => item.status === 'sent').length ?? 0
  const todos = candidateTodos(profile)
  const done = todos.filter((item) => item.done).length
  const hidden = profile.jobStatus === 'not_looking'

  return (
    <section className="cabinet-hero cabinet-hero--candidate" aria-labelledby="page-title">
      <span className="cabinet-hero__glyph" aria-hidden="true">
        [<span>•</span>]
      </span>
      <div className="cabinet-hero__main">
        <span className="cabinet-hero__kicker">Кабинет специалиста</span>
        <h1 id="page-title" className="cabinet-hero__title">
          {firstName}
        </h1>
        <p className="cabinet-hero__lead">
          {fresh > 0
            ? `Новых приглашений: ${fresh}. Ответьте — работодатель ждёт.`
            : 'Новых приглашений нет. Заполненный профиль чаще попадает в подборку работодателей.'}
        </p>
      </div>
      <div className="cabinet-hero__side">
        <p className="cabinet-hero__progress">
          <span>Профиль заполнен</span>
          <b>{Math.round((done / todos.length) * 100)}%</b>
        </p>
        <div className="cabinet-hero__cells" aria-hidden="true">
          {todos.map((item, index) => (
            <span key={item.id} className={index < done ? 'is-done' : undefined} />
          ))}
        </div>
        <div className="cabinet-hero__chips">
          <span className="cabinet-hero__chip cabinet-hero__chip--dark">
            {category ?? 'Категория после теста'}
          </span>
          <Link className="cabinet-hero__chip" to={ROUTES.profileSettings}>
            <span className={hidden ? 'cabinet-dot is-off' : 'cabinet-dot'} aria-hidden="true" />
            {hidden ? 'Профиль скрыт' : 'Профиль виден'}
          </Link>
        </div>
      </div>
    </section>
  )
}
