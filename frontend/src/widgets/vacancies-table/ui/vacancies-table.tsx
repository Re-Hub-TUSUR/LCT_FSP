import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router'
import { vacancyQueries, WORK_FORMAT_LABELS } from '@/entities/vacancy'
import type { VacancyListParams } from '@/entities/vacancy'
import { paths } from '@/shared/config'
import { formatDate, formatRubRange } from '@/shared/lib'
import { QueryState } from '@/shared/ui'
import './vacancies-table.css'

export function VacanciesTable({ params }: { params: VacancyListParams }) {
  const query = useQuery(vacancyQueries.list(params))

  return (
    <QueryState
      query={query}
      isEmpty={(page) => page.items.length === 0}
      emptyTitle="Вакансий по выбранным условиям нет"
    >
      {(page) => (
        <div className="vacancies-table__scroll">
          <table className="vacancies-table">
            <caption className="visually-hidden">Опубликованные вакансии</caption>
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
              {page.items.map((vacancy) => (
                <tr key={vacancy.id}>
                  <td>{vacancy.title}</td>
                  <td>
                    <Link to={paths.company(vacancy.company.id)}>{vacancy.company.name}</Link>
                  </td>
                  <td>{vacancy.category.label}</td>
                  <td>{formatRubRange(vacancy.salary.from, vacancy.salary.to)}</td>
                  <td>{WORK_FORMAT_LABELS[vacancy.workFormat]}</td>
                  <td>{vacancy.publishedAt ? formatDate(vacancy.publishedAt) : 'Черновик'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </QueryState>
  )
}
