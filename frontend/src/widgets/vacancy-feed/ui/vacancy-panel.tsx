import { useQuery } from '@tanstack/react-query'
import { useId, type ReactNode } from 'react'
import { Link } from 'react-router'
import { companyQueries } from '@/entities/company'
import type { VacancyMatchDto } from '@/entities/vacancy'
import { SALARY_NOTE, WORK_FORMAT_LABELS } from '@/entities/vacancy'
import { paths } from '@/shared/config'
import { formatDate, formatRubRange, isHttpUrl } from '@/shared/lib'
import { Sheet, SheetSection, VerifiedMark } from '@/shared/ui'
import './vacancy-sheet.css'

type Props = {
  match: VacancyMatchDto
  profileStack: readonly string[]
  onClose: () => void
  actions?: ReactNode
}

/** Right-hand sheet on the feed page: the whole vacancy and its company, scrolling. */
export function VacancyPanel({ match, profileStack, onClose, actions }: Props) {
  const { vacancy } = match
  const titleId = useId()
  const company = useQuery(companyQueries.detail(vacancy.company.id))
  const website = company.data?.website
  const owned = new Set(profileStack.map((item) => item.toLocaleLowerCase('ru')))
  const blocks = vacancy.description.split('\n\n').filter(Boolean)
  const companyLine = [
    company.data?.city ?? vacancy.company.city,
    company.data?.size ?? vacancy.company.size,
  ]
    .filter(Boolean)
    .join(' · ')

  return (
    <Sheet label="Вакансия" labelledBy={titleId} onClose={onClose} footer={actions}>
      <div className="vacancy-panel__head">
        <p className="vacancy-panel__company">
          <Link to={paths.company(vacancy.company.id)}>
            <b>{vacancy.company.name}</b>
          </Link>
          {vacancy.company.itAccredited && <VerifiedMark />}
          {vacancy.company.industry && <span> · {vacancy.company.industry}</span>}
        </p>
        <h2 id={titleId} className="vacancy-panel__title">
          {vacancy.title}
        </h2>
        <p className="vacancy-panel__salary">
          {formatRubRange(vacancy.salary.from, vacancy.salary.to)}
          <span> {SALARY_NOTE}</span>
        </p>
        {match.matched && <p className="vacancy-row__match">Взаимно: компания отобрала вас</p>}
      </div>

      <ul className="vacancy-row__chips">
        <li className="is-accent">{vacancy.category.label}</li>
        <li>{WORK_FORMAT_LABELS[vacancy.workFormat]}</li>
        {vacancy.city && <li>{vacancy.city}</li>}
        {vacancy.company.size && <li>{vacancy.company.size} чел.</li>}
      </ul>

      {blocks.length > 0 && (
        <SheetSection title="Описание">
          {blocks.map((block) => (
            <p key={block} className="vacancy-panel__text">
              {block}
            </p>
          ))}
        </SheetSection>
      )}

      {vacancy.stack.length > 0 && (
        <SheetSection title="Стек">
          <ul className="vacancy-panel__skills" aria-label="Навыки">
            {vacancy.stack.map((skill) => (
              <li
                key={skill}
                className={owned.has(skill.toLocaleLowerCase('ru')) ? 'is-known' : undefined}
              >
                {skill}
              </li>
            ))}
          </ul>
        </SheetSection>
      )}

      <SheetSection title="О компании">
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
      </SheetSection>

      {vacancy.publishedAt && (
        <p className="sheet-note">Опубликована {formatDate(vacancy.publishedAt)}</p>
      )}
    </Sheet>
  )
}
