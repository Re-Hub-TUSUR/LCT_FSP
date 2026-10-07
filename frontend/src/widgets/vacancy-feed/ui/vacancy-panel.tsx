import { useQuery } from '@tanstack/react-query'
import {
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
  type CSSProperties,
  type ReactNode,
} from 'react'
import { companyQueries } from '@/entities/company'
import type { VacancyMatchDto } from '@/entities/vacancy'
import { WORK_FORMAT_LABELS } from '@/entities/vacancy'
import { formatDate, formatRubRange, isHttpUrl, useSheetWidth } from '@/shared/lib'
import './vacancy-sheet.css'

type Props = {
  match: VacancyMatchDto
  profileStack: readonly string[]
  onClose: () => void
  actions?: ReactNode
}

/** Right-hand sheet on the feed page. Sized to the screen; a long description fades instead of scrolling. */
export function VacancyPanel({ match, profileStack, onClose, actions }: Props) {
  const { vacancy } = match
  const titleId = useId()
  const closeRef = useRef<HTMLButtonElement>(null)
  const copyRef = useRef<HTMLDivElement>(null)
  const [clipped, setClipped] = useState(false)
  const [leaving, setLeaving] = useState(false)
  const company = useQuery(companyQueries.detail(vacancy.company.id))
  const website = company.data?.website
  const owned = new Set(profileStack.map((item) => item.toLocaleLowerCase('ru')))
  const blocks = vacancy.description.split('\n\n').filter(Boolean)
  const [panelRef, sheet] = useSheetWidth(
    `${vacancy.id}:${blocks.length}:${vacancy.stack.length}:${company.data?.description?.length ?? 0}`,
  )
  const companyLine = [
    company.data?.city ?? vacancy.company.city,
    company.data?.size ?? vacancy.company.size,
  ]
    .filter(Boolean)
    .join(' · ')

  const requestClose = useCallback(() => {
    if (leaving) return
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (reduceMotion) {
      onClose()
      return
    }
    setLeaving(true)
  }, [leaving, onClose])

  useEffect(() => {
    closeRef.current?.focus()
  }, [])

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') requestClose()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [requestClose])

  useEffect(() => {
    if (!leaving) return
    const timer = window.setTimeout(onClose, 700)
    return () => window.clearTimeout(timer)
  }, [leaving, onClose])

  useEffect(() => {
    const element = copyRef.current
    if (!element || sheet < 0) return
    const measure = () => setClipped(element.scrollHeight > element.clientHeight + 1)
    measure()
    if (typeof ResizeObserver === 'undefined') return
    const observer = new ResizeObserver(measure)
    observer.observe(element)
    return () => observer.disconnect()
  }, [sheet])

  return (
    <>
      <button
        type="button"
        className={leaving ? 'vacancy-panel__scrim is-leaving' : 'vacancy-panel__scrim'}
        aria-label="Закрыть"
        onClick={requestClose}
      />
      <aside
        ref={panelRef}
        className={leaving ? 'vacancy-panel is-leaving' : 'vacancy-panel'}
        style={{ '--sheet': `${sheet}vw` } as CSSProperties}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onAnimationEnd={(event) => {
          if (
            event.target === event.currentTarget &&
            leaving &&
            event.animationName === 'vacancy-panel-out'
          ) {
            onClose()
          }
        }}
      >
        <header className="vacancy-panel__bar">
          <p className="vacancy-panel__label">Вакансия</p>
          <button
            ref={closeRef}
            type="button"
            className="vacancy-panel__close"
            onClick={requestClose}
          >
            Закрыть
          </button>
        </header>
        <div className="vacancy-panel__body">
          <div className="vacancy-panel__facts" data-fit="">
            <p className="vacancy-panel__company">
              <b>{vacancy.company.name}</b>
              {vacancy.company.industry && <span> · {vacancy.company.industry}</span>}
            </p>
            <h2 id={titleId} className="vacancy-panel__title">
              {vacancy.title}
            </h2>
            <p className="vacancy-panel__salary">
              {formatRubRange(vacancy.salary.from, vacancy.salary.to)}
              <span> в месяц</span>
            </p>
            <ul className="vacancy-row__chips">
              <li>{vacancy.category.label}</li>
              <li>{WORK_FORMAT_LABELS[vacancy.workFormat]}</li>
              {vacancy.city && <li>{vacancy.city}</li>}
              {vacancy.company.size && <li>{vacancy.company.size} чел.</li>}
            </ul>
            <ul className="vacancy-panel__skills" data-fit="" aria-label="Навыки">
              {vacancy.stack.map((skill) => (
                <li
                  key={skill}
                  className={owned.has(skill.toLocaleLowerCase('ru')) ? 'is-known' : undefined}
                >
                  {skill}
                </li>
              ))}
            </ul>
            <div className="vacancy-panel__about">
              <p className="vacancy-panel__label">О компании</p>
              {company.isPending && <p className="vacancy-panel__meta">Загружаем карточку</p>}
              {company.isError && (
                <p className="vacancy-panel__meta">Не удалось загрузить карточку компании</p>
              )}
              {company.data?.description && <p>{company.data.description}</p>}
              {companyLine && <p className="vacancy-panel__meta">{companyLine}</p>}
              {company.data?.contactEmail && (
                <p className="vacancy-panel__meta">{company.data.contactEmail}</p>
              )}
              {website && isHttpUrl(website) && (
                <a className="vacancy-panel__meta" href={website} target="_blank" rel="noreferrer">
                  {website}
                </a>
              )}
            </div>
          </div>
          <div
            ref={copyRef}
            data-fit=""
            className={clipped ? 'vacancy-panel__copy is-clipped' : 'vacancy-panel__copy'}
          >
            {blocks.map((block) => (
              <p key={block}>{block}</p>
            ))}
            {vacancy.publishedAt && (
              <p className="vacancy-panel__meta">Опубликована {formatDate(vacancy.publishedAt)}</p>
            )}
          </div>
        </div>
        {actions && <footer className="vacancy-panel__foot">{actions}</footer>}
      </aside>
    </>
  )
}
