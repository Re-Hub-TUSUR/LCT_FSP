import type { ReactNode } from 'react'
import { useState } from 'react'
import { formatRubRange, useOverflows } from '@/shared/lib'
import { MatchMeter } from '@/shared/ui'
import type { VacancyMatchDto } from '../api/vacancy-api'
import { WORK_FORMAT_LABELS } from '../model/work-format'

type Props = {
  match: VacancyMatchDto
  /** Like / skip buttons from the feature layer. */
  actions?: ReactNode
  /** Swipe deck shows the full description right away. */
  expanded?: boolean
  /** One film frame. The details button appears only when the text does not fit. */
  frame?: boolean
  /** Opens the side sheet. Used by the film frame. */
  onStudy?: () => void
}

export function VacancyMatchCard({
  match,
  actions,
  expanded = false,
  frame = false,
  onStudy,
}: Props) {
  const { vacancy, matchScore, reasons, matched } = match
  const [open, setOpen] = useState(expanded)
  const blocks = vacancy.description.split('\n\n').filter(Boolean)
  const [lead, ...rest] = blocks
  const place = vacancy.city ?? 'Любой город'
  const [bodyRef, overflows] = useOverflows(frame ? `${vacancy.id}:${blocks.length}` : '')

  const facts = (
    <ul className="match-card__facts">
      <li className="match-card__fact match-card__fact--accent">{vacancy.category.label}</li>
      <li className="match-card__fact">{WORK_FORMAT_LABELS[vacancy.workFormat]}</li>
      <li className="match-card__fact">{place}</li>
      {vacancy.company.size && <li className="match-card__fact">{vacancy.company.size} чел.</li>}
    </ul>
  )

  if (frame) {
    return (
      <article className="match-card match-card--frame" aria-label={vacancy.title}>
        <div
          ref={bodyRef}
          className={overflows ? 'match-card__frame-body is-clipped' : 'match-card__frame-body'}
        >
          <header className="match-card__head">
            <div className="match-card__titles">
              <p className="match-card__eyebrow">
                {vacancy.company.name}
                {vacancy.company.industry && <span> · {vacancy.company.industry}</span>}
              </p>
              <h3 className="match-card__title">{vacancy.title}</h3>
              {matched && <p className="match-card__matched">Взаимно: компания отобрала вас</p>}
            </div>
            {matchScore !== null && <MatchMeter value={matchScore} label="Соответствие" />}
          </header>
          <p className="match-card__salary">
            {formatRubRange(vacancy.salary.from, vacancy.salary.to)}
          </p>
          {facts}
          <ul className="match-card__stack" aria-label="Стек">
            {vacancy.stack.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          {reasons.length > 0 && (
            <section className="match-card__why" aria-label="Почему эта вакансия в ленте">
              <p className="match-card__why-title">Почему в ленте</p>
              <ul>
                {reasons.map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>
            </section>
          )}
          {blocks.length > 0 && (
            <div className="match-card__lead">
              {blocks.map((block) => (
                <p key={block}>{block}</p>
              ))}
            </div>
          )}
        </div>
        {overflows && onStudy && (
          <button type="button" className="match-card__more match-card__study" onClick={onStudy}>
            Изучить подробнее
          </button>
        )}
      </article>
    )
  }

  return (
    <article className="match-card" aria-label={vacancy.title}>
      <header className="match-card__head">
        <div className="match-card__titles">
          <p className="match-card__eyebrow">
            {vacancy.company.name}
            {vacancy.company.industry && <span> · {vacancy.company.industry}</span>}
          </p>
          <h3 className="match-card__title">{vacancy.title}</h3>
          {matched && <p className="match-card__matched">Взаимно: компания отобрала вас</p>}
          <p className="match-card__salary">
            {formatRubRange(vacancy.salary.from, vacancy.salary.to)}
          </p>
        </div>
        {matchScore !== null && <MatchMeter value={matchScore} label="Соответствие" />}
      </header>

      {facts}

      <ul className="match-card__stack" aria-label="Стек">
        {vacancy.stack.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>

      {reasons.length > 0 && (
        <section className="match-card__why" aria-label="Почему эта вакансия в ленте">
          <p className="match-card__why-title">Почему в ленте</p>
          <ul>
            {reasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        </section>
      )}

      <div className="match-card__text">
        {lead && <p>{lead}</p>}
        {open && rest.map((block) => <p key={block}>{block}</p>)}
        {rest.length > 0 && !expanded && (
          <button
            type="button"
            className="match-card__more"
            onClick={() => setOpen((value) => !value)}
          >
            {open ? 'Свернуть' : 'Подробнее о вакансии'}
          </button>
        )}
      </div>

      {actions && <footer className="match-card__actions">{actions}</footer>}
    </article>
  )
}
