import { useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import { companyQueries } from '@/entities/company/@x/vacancy'
import { formatRubRange, isHttpUrl } from '@/shared/lib'
import { MatchMeter } from '@/shared/ui'
import type { VacancyDto, VacancyMatchDto } from '../api/vacancy-api'
import { WORK_FORMAT_LABELS } from '../model/work-format'

type Props = {
  match: VacancyMatchDto
  /** Like / skip buttons from the feature layer. */
  actions?: ReactNode
  /** Swipe deck shows the full description right away. */
  expanded?: boolean
  /** One film frame: the short card, details live in a company dialog. */
  frame?: boolean
}

const FRAME_REASONS = 5

/**
 * Everything about a vacancy on one sheet that fits the screen: nothing in it scrolls.
 * The facts and the company are on the left, the description on the right.
 */
function VacancyDossier({ vacancy, onClose }: { vacancy: VacancyDto; onClose: () => void }) {
  const ref = useRef<HTMLDialogElement>(null)
  const body = useRef<HTMLDivElement>(null)
  const [clipped, setClipped] = useState(false)
  const company = useQuery(companyQueries.detail(vacancy.company.id))
  const website = company.data?.website
  const blocks = vacancy.description.split('\n\n').filter(Boolean)
  const place = vacancy.city ?? 'Любой город'

  useEffect(() => {
    const dialog = ref.current
    if (!dialog || dialog.open) return
    // Environments without the modal API (old browsers, jsdom) still get an open dialog.
    if (typeof dialog.showModal === 'function') dialog.showModal()
    else dialog.setAttribute('open', '')
  }, [])

  // A click on the backdrop lands on the dialog itself; unmounting closes it.
  useEffect(() => {
    const dialog = ref.current
    if (!dialog) return
    const onPointer = (event: MouseEvent) => {
      if (event.target === dialog) onClose()
    }
    dialog.addEventListener('click', onPointer)
    return () => dialog.removeEventListener('click', onPointer)
  }, [onClose])

  // An unusually long description is cut with a fade instead of getting a scrollbar.
  useEffect(() => {
    const element = body.current
    if (!element) return
    const measure = () => setClipped(element.scrollHeight > element.clientHeight + 1)
    measure()
    if (typeof ResizeObserver === 'undefined') return
    const observer = new ResizeObserver(measure)
    observer.observe(element)
    return () => observer.disconnect()
  }, [])

  return (
    <dialog ref={ref} className="vacancy-dossier" aria-labelledby="dossier-title" onClose={onClose}>
      <div className="vacancy-dossier__side">
        <header className="vacancy-dossier__head">
          <p className="match-card__eyebrow">
            {vacancy.company.name}
            {vacancy.company.industry && <span> · {vacancy.company.industry}</span>}
          </p>
          <button type="button" className="match-card__more" onClick={onClose}>
            Закрыть
          </button>
        </header>
        <h2 id="dossier-title" className="vacancy-dossier__title">
          {vacancy.title}
        </h2>
        <p className="match-card__salary">
          {formatRubRange(vacancy.salary.from, vacancy.salary.to)}
        </p>
        <ul className="match-card__facts">
          <li className="match-card__fact match-card__fact--accent">{vacancy.category.label}</li>
          <li className="match-card__fact">{WORK_FORMAT_LABELS[vacancy.workFormat]}</li>
          <li className="match-card__fact">{place}</li>
          {vacancy.company.size && (
            <li className="match-card__fact">{vacancy.company.size} чел.</li>
          )}
        </ul>
        <ul className="match-card__stack" aria-label="Стек">
          {vacancy.stack.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>

        <div className="vacancy-dossier__company">
          {company.isPending && (
            <p className="vacancy-dossier__meta">Загружаем карточку компании</p>
          )}
          {company.isError && (
            <p className="vacancy-dossier__meta">Не удалось загрузить карточку компании</p>
          )}
          {company.data?.description && (
            <p className="vacancy-dossier__about">{company.data.description}</p>
          )}
          {company.data?.contactEmail && (
            <p className="vacancy-dossier__meta">{company.data.contactEmail}</p>
          )}
          {website && isHttpUrl(website) && (
            <a className="vacancy-dossier__meta" href={website} target="_blank" rel="noreferrer">
              {website}
            </a>
          )}
        </div>
      </div>

      <div
        ref={body}
        className={clipped ? 'vacancy-dossier__body is-clipped' : 'vacancy-dossier__body'}
      >
        {blocks.map((block) => (
          <p key={block} className="vacancy-dossier__text">
            {block}
          </p>
        ))}
      </div>
    </dialog>
  )
}

export function VacancyMatchCard({ match, actions, expanded = false, frame = false }: Props) {
  const { vacancy, matchScore, reasons, matched } = match
  const [open, setOpen] = useState(expanded)
  const [dossier, setDossier] = useState(false)
  const [lead, ...rest] = vacancy.description.split('\n\n')
  const place = vacancy.city ?? 'Любой город'
  const shownReasons = frame ? reasons.slice(0, FRAME_REASONS) : reasons

  return (
    <article
      className={frame ? 'match-card match-card--frame' : 'match-card'}
      aria-label={vacancy.title}
    >
      <header className="match-card__head">
        <div className="match-card__titles">
          <p className="match-card__eyebrow">
            {vacancy.company.name}
            {vacancy.company.industry && <span> · {vacancy.company.industry}</span>}
          </p>
          <h3 className="match-card__title">{vacancy.title}</h3>
          {matched && <p className="match-card__matched">Взаимно: компания отобрала вас</p>}
          {!frame && (
            <p className="match-card__salary">
              {formatRubRange(vacancy.salary.from, vacancy.salary.to)}
            </p>
          )}
        </div>
        {matchScore !== null && <MatchMeter value={matchScore} label="Соответствие" />}
      </header>

      {frame && (
        <div className="match-card__pay">
          <p className="match-card__salary">
            {formatRubRange(vacancy.salary.from, vacancy.salary.to)}
          </p>
          <button type="button" className="match-card__more" onClick={() => setDossier(true)}>
            Изучить подробнее
          </button>
        </div>
      )}

      <ul className="match-card__facts">
        <li className="match-card__fact match-card__fact--accent">{vacancy.category.label}</li>
        <li className="match-card__fact">{WORK_FORMAT_LABELS[vacancy.workFormat]}</li>
        <li className="match-card__fact">{place}</li>
        {vacancy.company.size && <li className="match-card__fact">{vacancy.company.size} чел.</li>}
      </ul>

      <ul className="match-card__stack" aria-label="Стек">
        {vacancy.stack.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>

      {frame && lead && (
        <p className="match-card__lead">{[lead, rest[0]].filter(Boolean).join('\n\n')}</p>
      )}

      {shownReasons.length > 0 && (
        <section className="match-card__why" aria-label="Почему эта вакансия в ленте">
          <p className="match-card__why-title">Почему в ленте</p>
          <ul>
            {shownReasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        </section>
      )}

      {!frame && (
        <div className="match-card__text">
          <p>{lead}</p>
          {open && rest.map((block) => <p key={block}>{block}</p>)}
          {rest.length > 0 && !expanded && (
            <button type="button" className="match-card__more" onClick={() => setOpen((v) => !v)}>
              {open ? 'Свернуть' : 'Подробнее о вакансии'}
            </button>
          )}
        </div>
      )}

      {frame && dossier && <VacancyDossier vacancy={vacancy} onClose={() => setDossier(false)} />}

      {actions && <footer className="match-card__actions">{actions}</footer>}
    </article>
  )
}
