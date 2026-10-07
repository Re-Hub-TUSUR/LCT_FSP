import { useState } from 'react'
import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { Chip, EmptyState, ErrorState, Loader } from '@/shared/ui'
import { adminQueries } from '../../api/admin-api'
import type { Period, TaskFlag } from '../../api/types'
import { errorText, formatDuration, formatPercent, formatPp, gradeLabel } from '../../lib/format'
import { FLAG_LABELS, KIND_LABELS, STATUS_LABELS } from '../../lib/labels'
import { useParam } from '../../lib/use-param'
import { Pager } from '../common/pager'
import { SnapshotBar } from '../common/snapshot-bar'
import { TaskAnalyticsCard } from './task-analytics-card'

export function TaskAnalyticsSection() {
  const [taskId, setTaskId] = useParam('task')
  const [period, setPeriod] = useState<Period>('90d')
  const [flag, setFlag] = useParam('flag')
  const [page, setPage] = useState(1)
  const table = useQuery({
    ...adminQueries.taskTable({ period, page, flag: flag ?? undefined }),
    placeholderData: keepPreviousData,
  })
  const dictionaries = useQuery(adminQueries.dictionaries())

  if (taskId) {
    return (
      <TaskAnalyticsCard
        taskId={taskId}
        period={period}
        onPeriod={setPeriod}
        onBack={() => setTaskId(null)}
      />
    )
  }

  const summary = table.data?.summary
  const rules = table.data?.rules
  const chooseFlag = (value: string | null) => {
    setPage(1)
    setFlag(value)
  }

  return (
    <section className="admin-section">
      <header className="admin-section__head">
        <h1 className="admin-section__title">Аналитика заданий</h1>
      </header>
      <SnapshotBar
        block="tasks"
        period={period}
        onPeriod={(value) => {
          setPage(1)
          setPeriod(value)
        }}
        snapshot={table.data?.snapshot}
        exports={[{ table: 'tasks', label: 'задания' }]}
      />

      {summary && (
        <div className="tiles" role="group" aria-label="Флаги">
          <button
            type="button"
            className={`tile${flag === null ? ' is-active' : ''}`}
            onClick={() => chooseFlag(null)}
          >
            <span className="tile__value">{summary.tasks}</span>
            <span className="tile__label">заданий, {summary.withAttempts} с попытками</span>
          </button>
          {(Object.keys(FLAG_LABELS) as TaskFlag[]).map((code) => (
            <button
              key={code}
              type="button"
              className={`tile tile--flag${flag === code ? ' is-active' : ''}`}
              onClick={() => chooseFlag(code)}
            >
              <span className="tile__value">{summary.flags[code] ?? 0}</span>
              <span className="tile__label">{FLAG_LABELS[code]}</span>
            </button>
          ))}
        </div>
      )}
      {rules && (
        <p className="admin-hint">
          Флаги ставятся при {rules.minAttempts}+ попытках: целевая доля решивших {rules.targetMin}–
          {rules.targetMax}%, разброс вариантов &gt; {rules.spreadPp} п.п., рост за неделю &gt;{' '}
          {rules.leakPp} п.п. Пороги меняются в «Справочниках и параметрах» и применяются при
          следующем пересчёте.
        </p>
      )}

      {table.isPending ? (
        <Loader />
      ) : table.isError ? (
        <ErrorState message={errorText(table.error)} onRetry={() => void table.refetch()} />
      ) : !table.data.snapshot ? (
        <EmptyState title="Данных пока нет">
          Нажмите «Пересчитать»: метрики считаются только по запросу и сохраняются.
        </EmptyState>
      ) : table.data.items.length === 0 ? (
        <EmptyState title="Нет заданий с этим флагом">
          <Chip onClick={() => chooseFlag(null)}>Показать все</Chip>
        </EmptyState>
      ) : (
        <>
          <div className="admin-table-wrap">
            <table className="admin-table admin-table--numbers">
              <thead>
                <tr>
                  <th scope="col">Задание</th>
                  <th scope="col">Статус</th>
                  <th scope="col">Попыток</th>
                  <th scope="col">Полностью</th>
                  <th scope="col">Частично</th>
                  <th scope="col">Бросили</th>
                  <th scope="col">Среднее время</th>
                  <th scope="col">Медиана</th>
                  <th scope="col">Разброс</th>
                  <th scope="col">Рост за неделю</th>
                  <th scope="col">Флаги</th>
                </tr>
              </thead>
              <tbody>
                {table.data.items.map((row) => (
                  <tr key={row.taskId}>
                    <td>
                      <button
                        type="button"
                        className="admin-link"
                        onClick={() => setTaskId(row.taskId)}
                      >
                        {row.title}
                      </button>
                      <span className="admin-sub">
                        {KIND_LABELS[row.kind]} ·{' '}
                        {gradeLabel(row.grade, dictionaries.data?.grades ?? [])} · {row.skill}
                      </span>
                    </td>
                    <td>
                      <span className={`status status--${row.status}`}>
                        {STATUS_LABELS[row.status]}
                      </span>
                    </td>
                    <td>{row.attempts}</td>
                    <td>{formatPercent(row.fullShare)}</td>
                    <td>{formatPercent(row.partialShare)}</td>
                    <td>{formatPercent(row.abandonedShare)}</td>
                    <td>{formatDuration(row.avgTimeSec)}</td>
                    <td>{formatDuration(row.medianTimeSec)}</td>
                    <td>{formatPp(row.variantSpreadPp)}</td>
                    <td>{formatPp(row.maxWeeklyJumpPp)}</td>
                    <td>
                      {row.flags.map((code) => (
                        <span key={code} className={`flag flag--${code}`}>
                          {FLAG_LABELS[code]}
                        </span>
                      ))}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pager
            page={table.data.page}
            pages={table.data.pages}
            total={table.data.total}
            onPage={setPage}
          />
        </>
      )}
    </section>
  )
}
