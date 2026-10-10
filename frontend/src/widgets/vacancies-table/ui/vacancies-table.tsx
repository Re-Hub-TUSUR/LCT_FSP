import { useState } from 'react'
import type { FormEvent } from 'react'
import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router'
import { categoryQueries, GRADE_LABELS, GRADES } from '@/entities/category'
import type { Grade } from '@/entities/category'
import { companyQueries } from '@/entities/company'
import { useSession } from '@/entities/session'
import { vacancyQueries, WORK_FORMAT_LABELS, WORK_FORMATS } from '@/entities/vacancy'
import type { VacancyDto, WorkFormat } from '@/entities/vacancy'
import { paths } from '@/shared/config'
import { formatDate, formatRubRange, plural } from '@/shared/lib'
import { EmptyState, Pagination, QueryState, Segmented, Tag, VerifiedMark } from '@/shared/ui'
import { VacancySheet } from './vacancy-sheet'
import './vacancies-table.css'

const FORMAT_ITEMS = [
  { value: 'any', label: 'Любой' },
  ...WORK_FORMATS.map((format) => ({ value: format, label: WORK_FORMAT_LABELS[format] })),
] as const

const isGrade = (value: string | null): value is Grade => GRADES.includes(value as Grade)
const isFormat = (value: string | null): value is WorkFormat =>
  WORK_FORMATS.includes(value as WorkFormat)

/** A company's own vacancy under the same filters the public list is asked with. */
function matches(
  vacancy: VacancyDto,
  filter: { q: string; specialization: string; grade?: Grade; workFormat?: WorkFormat },
) {
  if (filter.specialization && vacancy.category.specialization !== filter.specialization) {
    return false
  }
  if (
    filter.grade &&
    !(vacancy.grades.includes(filter.grade) || vacancy.category.grade === filter.grade)
  ) {
    return false
  }
  if (filter.workFormat && vacancy.workFormat !== filter.workFormat) return false
  if (!filter.q) return true
  const text = [vacancy.title, vacancy.company.name, ...vacancy.stack].join(' ').toLowerCase()
  return filter.q
    .toLowerCase()
    .split(/\s+/)
    .every((token) => text.includes(token))
}

/**
 * Vacancies with filters in the URL; a row opens the whole vacancy in the side sheet. A candidate
 * sees every published vacancy, a company only its own, drafts included.
 */
export function VacanciesTable() {
  const { user } = useSession()
  const employer = user?.role === 'employer'
  const [params, setParams] = useSearchParams()
  const page = Math.max(1, Number(params.get('page')) || 1)
  const perPage = Number(params.get('perPage')) || 20
  const q = params.get('q') ?? ''
  const specialization = params.get('specialization') ?? ''
  const grade = isGrade(params.get('grade')) ? (params.get('grade') as Grade) : undefined
  const workFormat = isFormat(params.get('workFormat'))
    ? (params.get('workFormat') as WorkFormat)
    : undefined
  const [text, setText] = useState(q)
  const [open, setOpen] = useState<VacancyDto | null>(null)

  const dictionary = useQuery(categoryQueries.dictionary())
  const company = useQuery({ ...companyQueries.mine(), enabled: employer, retry: false })
  const mine = useQuery({ ...vacancyQueries.mine(), enabled: employer })
  const query = useQuery({
    ...vacancyQueries.list({
      search: q || undefined,
      specialization: specialization || undefined,
      grade,
      workFormat,
      page,
      perPage,
    }),
    placeholderData: keepPreviousData,
    enabled: !employer,
  })

  const update = (patch: Record<string, string | null>) => {
    const next = new URLSearchParams(params)
    for (const [key, value] of Object.entries(patch)) {
      if (value) next.set(key, value)
      else next.delete(key)
    }
    if (!('page' in patch)) next.delete('page')
    setParams(next, { replace: true })
  }

  const onSearch = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    update({ q: text.trim() || null })
  }

  const ownId = company.data?.id
  const isOwn = (vacancy: VacancyDto) => ownId !== undefined && vacancy.company.id === ownId

  return (
    <div className="vacancies">
      <div className="vacancies__filters">
        <form className="feed__search vacancies__search" role="search" onSubmit={onSearch}>
          <input
            aria-label="Поиск по вакансиям"
            placeholder="Название, компания или навык"
            value={text}
            onChange={(event) => setText(event.target.value)}
          />
          <button type="submit">Найти</button>
        </form>
        <select
          className="feed__select vacancies__select"
          aria-label="Специализация"
          value={specialization}
          onChange={(event) => update({ specialization: event.target.value || null })}
        >
          <option value="">Все специализации</option>
          {dictionary.data?.specializations.map((item) => (
            <option key={item.code} value={item.code}>
              {item.label}
            </option>
          ))}
        </select>
        <select
          className="feed__select vacancies__select"
          aria-label="Грейд"
          value={grade ?? ''}
          onChange={(event) => update({ grade: event.target.value || null })}
        >
          <option value="">Любой грейд</option>
          {GRADES.map((item) => (
            <option key={item} value={item}>
              {GRADE_LABELS[item]}
            </option>
          ))}
        </select>
        <Segmented
          label="Формат работы"
          items={FORMAT_ITEMS}
          value={workFormat ?? 'any'}
          onChange={(value) => update({ workFormat: value === 'any' ? null : value })}
        />
      </div>

      <QueryState query={employer ? mine : query}>
        {(data) => {
          // The company's own list comes whole (up to 100) and is filtered here.
          const rows = employer
            ? data.items.filter((vacancy) =>
                matches(vacancy, { q, specialization, grade, workFormat }),
              )
            : data.items
          const total = employer ? rows.length : data.total
          return (
            <>
              <p className="feed__found">
                <span className="feed__found-count">{total}</span>
                <span className="feed__label">
                  {plural(total, ['вакансия', 'вакансии', 'вакансий'])}
                </span>
              </p>
              {rows.length === 0 ? (
                <div className="feed-table">
                  <EmptyState title="Вакансий по выбранным условиям нет">
                    Уберите часть фильтров или измените запрос.
                  </EmptyState>
                </div>
              ) : (
                <div className="vacancies-table__scroll">
                  <table className="vacancies-table">
                    <caption className="visually-hidden">
                      {employer ? 'Вакансии компании' : 'Опубликованные вакансии'}
                    </caption>
                    <thead>
                      <tr>
                        <th scope="col">Вакансия</th>
                        <th scope="col">Компания</th>
                        <th scope="col">Категория</th>
                        <th scope="col">Зарплата</th>
                        <th scope="col">Формат</th>
                        <th scope="col">Опубликована</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rows.map((vacancy) => (
                        <tr
                          key={vacancy.id}
                          className={
                            [isOwn(vacancy) && 'is-own', open?.id === vacancy.id && 'is-open']
                              .filter(Boolean)
                              .join(' ') || undefined
                          }
                          onClick={() => setOpen(vacancy)}
                        >
                          <td data-label="Вакансия">
                            <button
                              type="button"
                              className="vacancies-table__title"
                              aria-expanded={open?.id === vacancy.id}
                              onClick={(event) => {
                                event.stopPropagation()
                                setOpen(vacancy)
                              }}
                            >
                              {vacancy.title}
                            </button>
                            {vacancy.stack.length > 0 && (
                              <span className="vacancies-table__stack">
                                {vacancy.stack.join(' · ')}
                              </span>
                            )}
                          </td>
                          <td data-label="Компания">
                            <span className="vacancies-table__company">
                              <Link
                                to={paths.company(vacancy.company.id)}
                                onClick={(event) => event.stopPropagation()}
                              >
                                {vacancy.company.name}
                              </Link>
                              {vacancy.company.itAccredited && <VerifiedMark />}
                              {isOwn(vacancy) && <span className="vacancies-table__own">Ваша</span>}
                            </span>
                          </td>
                          <td data-label="Категория">
                            <Tag>{vacancy.category.label}</Tag>
                          </td>
                          <td data-label="Зарплата" className="vacancies-table__salary">
                            {formatRubRange(vacancy.salary.from, vacancy.salary.to)}
                          </td>
                          <td data-label="Формат">
                            {[WORK_FORMAT_LABELS[vacancy.workFormat], vacancy.city]
                              .filter(Boolean)
                              .join(' · ')}
                          </td>
                          <td data-label="Опубликована">
                            {vacancy.publishedAt ? (
                              formatDate(vacancy.publishedAt)
                            ) : (
                              <span className="vacancies-table__draft">Черновик</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              {!employer && data.pages > 1 && (
                <Pagination
                  page={data.page}
                  pages={data.pages}
                  perPage={data.perPage}
                  total={data.total}
                  onPage={(next) => {
                    update({ page: String(next) })
                    window.scrollTo({ top: 0, behavior: 'smooth' })
                  }}
                  onPerPage={(size) => update({ perPage: String(size) })}
                />
              )}
            </>
          )
        }}
      </QueryState>

      {open && (
        <VacancySheet
          key={open.id}
          vacancy={open}
          own={isOwn(open)}
          onClose={() => setOpen(null)}
        />
      )}
    </div>
  )
}
