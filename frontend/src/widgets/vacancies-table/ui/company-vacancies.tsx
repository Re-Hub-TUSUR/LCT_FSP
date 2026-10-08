import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { companyQueries } from '@/entities/company'
import { useSession } from '@/entities/session'
import { vacancyQueries, WORK_FORMAT_LABELS } from '@/entities/vacancy'
import type { VacancyDto } from '@/entities/vacancy'
import { formatDate, formatRubRange, plural } from '@/shared/lib'
import { EmptyState, QueryState, Tag } from '@/shared/ui'
import { VacancySheet } from './vacancy-sheet'
import './vacancies-table.css'

/** Every published vacancy of one company; a row opens the whole vacancy in the side sheet. */
export function CompanyVacancies({ companyId }: { companyId: string }) {
  const { user } = useSession()
  const [open, setOpen] = useState<VacancyDto | null>(null)
  const vacancies = useQuery(vacancyQueries.list({ companyId, perPage: 100 }))
  const own = useQuery({
    ...companyQueries.mine(),
    enabled: user?.role === 'employer',
    retry: false,
  })

  return (
    <div className="vacancies">
      <QueryState query={vacancies}>
        {(data) =>
          data.items.length === 0 ? (
            <EmptyState title="Открытых вакансий сейчас нет" />
          ) : (
            <>
              <p className="feed__found">
                <span className="feed__found-count">{data.total}</span>
                <span className="feed__label">
                  {plural(data.total, ['вакансия', 'вакансии', 'вакансий'])}
                </span>
              </p>
              <div className="vacancies-table__scroll">
                <table className="vacancies-table">
                  <caption className="visually-hidden">Вакансии компании</caption>
                  <thead>
                    <tr>
                      <th scope="col">Вакансия</th>
                      <th scope="col">Категория</th>
                      <th scope="col">Зарплата</th>
                      <th scope="col">Формат</th>
                      <th scope="col">Опубликована</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.items.map((vacancy) => (
                      <tr
                        key={vacancy.id}
                        className={open?.id === vacancy.id ? 'is-open' : undefined}
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
                          {vacancy.publishedAt ? formatDate(vacancy.publishedAt) : ''}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )
        }
      </QueryState>

      {open && (
        <VacancySheet
          key={open.id}
          vacancy={open}
          own={own.data?.id === companyId}
          onClose={() => setOpen(null)}
        />
      )}
    </div>
  )
}
