import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Button, EmptyState, ErrorState, Loader } from '@/shared/ui'
import { adminApi, adminKeys, adminQueries } from '../../api/admin-api'
import type { Metrics, Period } from '../../api/types'
import {
  errorText,
  formatDuration,
  formatMonth,
  formatPercent,
  formatPp,
  formatWeek,
} from '../../lib/format'
import { FLAG_LABELS, STATUS_LABELS } from '../../lib/labels'
import { BarChart, LineChart } from '../common/charts'
import { ReasonDialog } from '../common/reason-dialog'
import { SnapshotBar } from '../common/snapshot-bar'

type Props = { taskId: string; period: Period; onPeriod: (p: Period) => void; onBack: () => void }

const GRADE_NAMES: Record<string, string> = {
  intern: 'Стажёр',
  junior: 'Junior',
  middle: 'Middle',
  senior: 'Senior',
  lead: 'Lead',
}

/** Five-minute buckets read better than sixty one-minute ones. */
function histogramBars(rows: { minute: number; count: number }[]) {
  const buckets = new Map<number, number>()
  for (const row of rows) {
    const start = Math.min(Math.floor(row.minute / 5) * 5, 60)
    buckets.set(start, (buckets.get(start) ?? 0) + row.count)
  }
  const bars: { label: string; value: number; hint: string }[] = []
  for (let start = 0; start <= 60; start += 5) {
    const count = buckets.get(start)
    if (!count) continue
    bars.push({
      label: start >= 60 ? '60+' : `${start}–${start + 5}`,
      value: count,
      hint: 'минут на попытку',
    })
  }
  return bars
}

function MetricsTable({
  rows,
  keyLabel,
}: {
  rows: (Metrics & { key: string })[]
  keyLabel: string
}) {
  return (
    <div className="admin-table-wrap">
      <table className="admin-table admin-table--numbers">
        <thead>
          <tr>
            <th scope="col">{keyLabel}</th>
            <th scope="col">Попыток</th>
            <th scope="col">Полностью</th>
            <th scope="col">Частично</th>
            <th scope="col">Бросили</th>
            <th scope="col">Не решили</th>
            <th scope="col">Среднее время</th>
            <th scope="col">Медиана</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.key}>
              <td>{row.key}</td>
              <td>{row.attempts}</td>
              <td>{formatPercent(row.fullShare)}</td>
              <td>{formatPercent(row.partialShare)}</td>
              <td>{formatPercent(row.abandonedShare)}</td>
              <td>{formatPercent(row.unsolvedShare)}</td>
              <td>{formatDuration(row.avgTimeSec)}</td>
              <td>{formatDuration(row.medianTimeSec)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function TaskAnalyticsCard({ taskId, period, onPeriod, onBack }: Props) {
  const queryClient = useQueryClient()
  const card = useQuery(adminQueries.taskCard(taskId, period))
  const task = useQuery(adminQueries.task(taskId))
  const parameters = useQuery(adminQueries.parameters())
  const [leaking, setLeaking] = useState(false)
  const markLeaked = useMutation({
    mutationFn: (reason: string) => adminApi.setTaskStatus(taskId, 'leaked', reason),
    onSuccess: () => {
      setLeaking(false)
      void queryClient.invalidateQueries({ queryKey: adminKeys.bank() })
      void queryClient.invalidateQueries({ queryKey: adminKeys.analytics() })
    },
  })

  const result = card.data?.result
  const value = (key: string) => parameters.data?.items.find((item) => item.key === key)?.value
  const targetMin = value('target_solve_min') ?? 50
  const targetMax = value('target_solve_max') ?? 70
  const canMarkLeaked =
    result?.flags.includes('possible_leak') && task.data?.allowedStatuses.includes('leaked')

  return (
    <section className="admin-section">
      <Button variant="ghost" size="inline" onClick={onBack}>
        ← Ко всем заданиям
      </Button>
      <header className="admin-section__head">
        <div>
          <h1 className="admin-section__title">{task.data?.title ?? 'Задание'}</h1>
          {task.data && (
            <p className="admin-meta">
              <span className={`status status--${task.data.status}`}>
                {STATUS_LABELS[task.data.status]}
              </span>
              {result?.flags.map((flag) => (
                <span key={flag} className={`flag flag--${flag}`}>
                  {FLAG_LABELS[flag]}
                </span>
              ))}
            </p>
          )}
        </div>
        {canMarkLeaked && (
          <div className="admin-section__actions">
            <Button size="inline" onClick={() => setLeaking(true)}>
              Отметить как утёкшее
            </Button>
          </div>
        )}
      </header>
      <SnapshotBar
        block="task_card"
        period={period}
        onPeriod={onPeriod}
        taskId={taskId}
        snapshot={card.data?.snapshot}
        exports={[
          { table: 'variants', label: 'варианты' },
          { table: 'grades', label: 'грейды' },
          { table: 'weekly', label: 'по неделям' },
          { table: 'monthly', label: 'по месяцам' },
          { table: 'histogram', label: 'время' },
        ]}
      />

      {card.isPending ? (
        <Loader />
      ) : card.isError ? (
        <ErrorState message={errorText(card.error)} onRetry={() => void card.refetch()} />
      ) : !result ? (
        <EmptyState title="Карточка ещё не считалась">
          Нажмите «Пересчитать», чтобы посчитать метрики задания за выбранный период.
        </EmptyState>
      ) : !result.overall ? (
        <EmptyState title="За период попыток нет">Выберите период длиннее.</EmptyState>
      ) : (
        <>
          <div className="tiles">
            {[
              ['Попыток', String(result.overall.attempts)],
              ['Решили полностью', formatPercent(result.overall.fullShare)],
              ['Частично', formatPercent(result.overall.partialShare)],
              ['Бросили', formatPercent(result.overall.abandonedShare)],
              ['Медиана времени', formatDuration(result.overall.medianTimeSec)],
              ['Разброс вариантов', formatPp(result.variantSpreadPp)],
              ['Рост за неделю', formatPp(result.maxWeeklyJumpPp)],
            ].map(([label, shown]) => (
              <div key={label} className="tile">
                <span className="tile__value">{shown}</span>
                <span className="tile__label">{label}</span>
              </div>
            ))}
          </div>
          <p className="admin-hint">
            Время — длительность всей попытки с этим заданием: время по отдельному заданию платформа
            не записывает.
          </p>

          <div className="admin-columns">
            <LineChart
              title="Доля решивших полностью по неделям"
              points={result.weekly.map((row) => ({
                label: formatWeek(row.week),
                value: row.fullShare,
                hint: `${row.attempts} попыток`,
              }))}
              band={{ from: targetMin, to: targetMax, label: `цель ${targetMin}–${targetMax}%` }}
              format={(v) => `${Math.round(v)}%`}
            />
            <BarChart
              title="Распределение времени, минут"
              bars={histogramBars(result.histogram)}
              format={(v) => String(Math.round(v))}
            />
            <BarChart
              title="Доля решивших полностью по заявленному грейду"
              bars={result.grades.map((row) => ({
                label: GRADE_NAMES[row.grade ?? ''] ?? 'без грейда',
                value: row.fullShare ?? 0,
                hint: `${row.attempts} попыток`,
              }))}
              max={100}
              format={(v) => `${Math.round(v)}%`}
            />
            <LineChart
              title="Доля решивших полностью по месяцам, всё время"
              points={result.monthly.map((row) => ({
                label: formatMonth(row.month),
                value: row.fullShare,
                hint: `${row.attempts} попыток`,
              }))}
              format={(v) => `${Math.round(v)}%`}
            />
          </div>

          <h2 className="admin-card__title">По вариантам</h2>
          <MetricsTable
            keyLabel="Вариант"
            rows={result.variants.map((row) => ({
              ...row,
              key: row.variant === 'base' ? 'основной' : row.variant,
            }))}
          />
          <h2 className="admin-card__title">По заявленному грейду</h2>
          <MetricsTable
            keyLabel="Грейд"
            rows={result.grades.map((row) => ({
              ...row,
              key: GRADE_NAMES[row.grade ?? ''] ?? 'без грейда',
            }))}
          />
          <h2 className="admin-card__title">По неделям</h2>
          <MetricsTable
            keyLabel="Неделя с"
            rows={result.weekly.map((row) => ({ ...row, key: formatWeek(row.week) }))}
          />
        </>
      )}

      {leaking && (
        <ReasonDialog
          title="Отметить задание как утёкшее"
          confirmLabel="Отметить"
          label="Признаки утечки"
          pending={markLeaked.isPending}
          error={markLeaked.isError ? errorText(markLeaked.error) : null}
          onConfirm={(reason) => markLeaked.mutate(reason)}
          onClose={() => setLeaking(false)}
        >
          <p className="admin-hint">
            Статус в банке станет «Утёк»: задание перестанет выдаваться кандидатам.
          </p>
        </ReasonDialog>
      )}
    </section>
  )
}
