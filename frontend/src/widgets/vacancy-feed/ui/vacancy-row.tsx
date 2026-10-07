import type { ReactNode } from 'react'
import type { VacancyMatchDto } from '@/entities/vacancy'
import { WORK_FORMAT_LABELS } from '@/entities/vacancy'
import { formatDate, formatRubRange } from '@/shared/lib'
import { VerifiedMark } from '@/shared/ui'
import './vacancy-sheet.css'

type Props = {
  match: VacancyMatchDto
  profileStack: readonly string[]
  selected: boolean
  onOpen: () => void
  actions?: ReactNode
}

function matchLine(match: VacancyMatchDto, profileStack: readonly string[]): string | null {
  const note = match.reasons.find((reason) =>
    /^(Смежная специализация:|Грейд .+ на ступень|Зарплата чуть ниже|Офис: .+переезду$)/.test(
      reason,
    ),
  )
  if (note) return note
  if (match.reasons.length > 0) return null
  const owned = new Set(profileStack.map((item) => item.toLocaleLowerCase('ru')))
  const hit = match.vacancy.stack.filter((item) => owned.has(item.toLocaleLowerCase('ru')))
  if (hit.length === 0) return null
  if (hit.length <= 3) {
    const list =
      hit.length < 2 ? hit.join('') : `${hit.slice(0, -1).join(', ')} и ${hit[hit.length - 1]}`
    return `${list} есть в вашем профиле`
  }
  return `${hit.length} из ${match.vacancy.stack.length} навыков есть в вашем профиле`
}

/** Short row in the vacancy feed. The full text opens in the side panel. */
export function VacancyRow({ match, profileStack, selected, onOpen, actions }: Props) {
  const { vacancy } = match
  const line = matchLine(match, profileStack)

  return (
    <article
      className={selected ? 'vacancy-row is-open' : 'vacancy-row'}
      aria-label={vacancy.title}
    >
      <button type="button" className="vacancy-row__open" aria-expanded={selected} onClick={onOpen}>
        <span className="vacancy-row__title">{vacancy.title}</span>
        <span className="vacancy-row__salary">
          {formatRubRange(vacancy.salary.from, vacancy.salary.to)}
        </span>
        <ul className="vacancy-row__chips">
          <li>{vacancy.category.label}</li>
          <li>{WORK_FORMAT_LABELS[vacancy.workFormat]}</li>
          {vacancy.city && <li>{vacancy.city}</li>}
        </ul>
        <p className="vacancy-row__company">
          <span className="vacancy-row__company-name">
            {vacancy.company.name}
            {vacancy.company.itAccredited && <VerifiedMark interactive={false} />}
          </span>
          {vacancy.company.industry && (
            <span className="vacancy-row__company-ind">{vacancy.company.industry}</span>
          )}
        </p>
        {match.matched && <p className="vacancy-row__match">Взаимно: компания отобрала вас</p>}
        {!match.matched && line && <p className="vacancy-row__match">{line}</p>}
      </button>
      <footer className="vacancy-row__foot">
        {actions}
        {vacancy.publishedAt && (
          <time className="vacancy-row__age" dateTime={vacancy.publishedAt}>
            {formatDate(vacancy.publishedAt)}
          </time>
        )}
      </footer>
    </article>
  )
}
