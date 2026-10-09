import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { EmptyState, ErrorState, Loader } from '@/shared/ui'
import { adminQueries } from '../../api/admin-api'
import type { Period } from '../../api/types'
import { errorText, formatNumber, formatPercent } from '../../lib/format'
import { Funnel } from '../common/charts'
import { SnapshotBar } from '../common/snapshot-bar'

export function PlatformSection() {
  const [period, setPeriod] = useState<Period>('90d')
  const platform = useQuery(adminQueries.platform(period))
  const result = platform.data?.result

  return (
    <section className="admin-section">
      <header className="admin-section__head">
        <h1 className="admin-section__title">Продуктовая аналитика</h1>
      </header>
      <SnapshotBar
        block="platform"
        period={period}
        onPeriod={setPeriod}
        snapshot={platform.data?.snapshot}
        exports={[
          { table: 'candidate_funnel', label: 'воронка кандидата' },
          { table: 'employer_funnel', label: 'воронка работодателя' },
          { table: 'demand', label: 'спрос и предложение' },
        ]}
      />
      <p className="admin-hint">
        Воронки — когорта зарегистрированных за период: сколько из них дошло до каждого шага.
        Метрики посещаемости сайта не собираются.
      </p>

      {platform.isPending ? (
        <Loader />
      ) : platform.isError ? (
        <ErrorState message={errorText(platform.error)} onRetry={() => void platform.refetch()} />
      ) : !result ? (
        <EmptyState title="Данных пока нет">Нажмите «Пересчитать».</EmptyState>
      ) : (
        <>
          <div className="admin-columns">
            <Funnel
              title="Воронка кандидата"
              steps={result.candidateFunnel.map((step) => ({
                label: step.label,
                count: step.count,
                share: step.fromStartShare,
              }))}
            />
            <Funnel
              title="Воронка работодателя"
              steps={result.employerFunnel.map((step) => ({
                label: step.label,
                count: step.count,
                share: step.fromStartShare,
              }))}
            />
          </div>

          <h2 className="admin-card__title">Востребованные категории: спрос и предложение</h2>
          {result.demand.length === 0 ? (
            <EmptyState title="Нет вакансий, приглашений и кандидатов с категорией" />
          ) : (
            <div className="admin-table-wrap">
              <table className="admin-table admin-table--numbers">
                <thead>
                  <tr>
                    <th scope="col">Категория</th>
                    <th scope="col">Поисков</th>
                    <th scope="col">Вакансий</th>
                    <th scope="col">Приглашений</th>
                    <th scope="col">Кандидатов</th>
                    <th scope="col">Спрос на кандидата</th>
                    <th scope="col">Дефицит</th>
                  </tr>
                </thead>
                <tbody>
                  {result.demand.map((row) => (
                    <tr key={`${row.specialization}:${row.grade}`}>
                      <td>
                        {row.specializationLabel} · {row.gradeLabel}
                      </td>
                      <td title="Поисковые запросы не логируются">{formatNumber(row.searches)}</td>
                      <td>{row.vacancies}</td>
                      <td>{row.invitations}</td>
                      <td>{row.candidates}</td>
                      <td>{row.deficit === null ? (row.demand ? '∞' : '—') : row.deficit}</td>
                      <td>
                        {row.shortage ? (
                          <span className="flag flag--possible_leak">Не хватает</span>
                        ) : (
                          '—'
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {result.gradeTests && (
            <>
              <h2 className="admin-card__title">Тесты на грейд</h2>
              <p className="admin-hint">
                Тесты, начатые за период. Доля сдавших считается от завершённых; «с расширением» — в
                банке не хватило заданий под правило шаблона. «Повышение» — тест грейдом выше уже
                подтверждённого у кандидата: если его сдают часто, тест плохо различает грейды.
              </p>
              <div className="admin-table-wrap">
                <table className="admin-table admin-table--numbers">
                  <thead>
                    <tr>
                      <th scope="col">Грейд</th>
                      <th scope="col">Начато</th>
                      <th scope="col">Завершено</th>
                      <th scope="col">Сдано</th>
                      <th scope="col">Доля сдавших</th>
                      <th scope="col">С расширением правил</th>
                      <th scope="col">Повышений</th>
                      <th scope="col">Сдано повышений</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.gradeTests.grades.map((row) => (
                      <tr key={row.grade}>
                        <td>{row.gradeLabel}</td>
                        <td>{row.started}</td>
                        <td>{row.settled}</td>
                        <td>{row.passed}</td>
                        <td>{formatPercent(row.passShare)}</td>
                        <td>{row.widened}</td>
                        <td>{row.stepUp ?? '—'}</td>
                        <td>
                          {row.stepUp
                            ? `${row.stepUpPassed} (${formatPercent(row.stepUpPassShare)})`
                            : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {result.gradeTests.shortages.length > 0 && (
                <>
                  <h3 className="admin-card__title">Чего не хватает в банке</h3>
                  <ul className="admin-list">
                    {result.gradeTests.shortages.map((item) => (
                      <li key={item.note}>
                        {item.note} — {item.count} раз
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </>
          )}
          <ul className="admin-list admin-hint">
            {result.missing.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </>
      )}
    </section>
  )
}
