import type { ReactNode } from 'react'
import { Tag } from '@/shared/ui'
import type { CandidateDto } from '../api/candidate-api'
import './candidate-card.css'

type Props = {
  candidate: CandidateDto
  /** Slot for actions provided by upper layers (invite, open profile, …). */
  actions?: ReactNode
}

export function CandidateCard({ candidate, actions }: Props) {
  const { displayName, headline, category, stack, experienceYears, fspAchievements, contacts } =
    candidate

  return (
    <article className="candidate-card" aria-label={displayName}>
      <header className="candidate-card__header">
        <h3 className="candidate-card__name">{displayName}</h3>
        {category && <Tag>{category.label}</Tag>}
      </header>

      {headline && <p className="candidate-card__headline">{headline}</p>}
      {experienceYears !== null && (
        <p className="candidate-card__meta">Опыт: {experienceYears} г.</p>
      )}

      {stack.length > 0 && (
        <ul className="candidate-card__stack" aria-label="Стек">
          {stack.map((item) => (
            <li key={item}>
              <Tag>{item}</Tag>
            </li>
          ))}
        </ul>
      )}

      <section className="candidate-card__fsp" aria-label="Достижения ФСП">
        {fspAchievements.length > 0 ? (
          <ul>
            {fspAchievements.map((item) => (
              <li key={`${item.eventName}-${item.year}`}>
                {item.eventName}, {item.year}
                {item.place !== null && ` — ${item.place} место`}
              </li>
            ))}
          </ul>
        ) : (
          <p className="candidate-card__meta">Нет подтверждённой истории участия в ФСП</p>
        )}
      </section>

      {contacts ? (
        <p className="candidate-card__meta">Контакты: {contacts.email}</p>
      ) : (
        <p className="candidate-card__meta">Контакты откроются после принятия приглашения</p>
      )}

      {actions && <footer className="candidate-card__actions">{actions}</footer>}
    </article>
  )
}
