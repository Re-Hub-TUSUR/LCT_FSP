import { useEffect, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Button, Chip } from '@/shared/ui'
import { adminApi, adminKeys } from '../../api/admin-api'
import type { Block, Period, SnapshotMeta } from '../../api/types'
import { errorText, formatStamp, retryAfter } from '../../lib/format'
import { PERIOD_LABELS } from '../../lib/labels'
import { ExportButton } from './export-button'

type ExportTable = { table: string; label: string }

type Props = {
  block: Block
  period: Period
  onPeriod: (period: Period) => void
  snapshot: SnapshotMeta | null | undefined
  taskId?: string
  exports?: ExportTable[]
}

/** True until `at`; flips once by a timer, so a cooled-down button unlocks. No data is fetched. */
function useCooling(at: string | null) {
  const [passed, setPassed] = useState<string | null>(null)
  useEffect(() => {
    if (!at) return
    const wait = new Date(at).getTime() - Date.now()
    const timer = setTimeout(() => setPassed(at), Math.max(wait, 0) + 200)
    return () => clearTimeout(timer)
  }, [at])
  return at !== null && passed !== at
}

/**
 * Period filter, «Пересчитать», the stamp of the stored data and CSV exports of it.
 * The analytics is computed only here, on a click; the button stays locked while the
 * calculation runs and for 5 minutes after it (the server enforces the same).
 */
export function SnapshotBar({ block, period, onPeriod, snapshot, taskId, exports = [] }: Props) {
  const queryClient = useQueryClient()
  const [lockedUntil, setLockedUntil] = useState<string | null>(null)
  const recalc = useMutation({
    mutationFn: () => adminApi.recalculate(block, period, taskId),
    onSuccess: () => {
      setLockedUntil(null)
      void queryClient.invalidateQueries({ queryKey: adminKeys.analytics() })
      if (block === 'employers') void queryClient.invalidateQueries({ queryKey: adminKeys.all })
    },
    onError: (error) => setLockedUntil(retryAfter(error)),
  })

  const until = lockedUntil ?? snapshot?.nextAllowedAt ?? null
  const cooling = useCooling(until)

  return (
    <div className="snapshot-bar">
      <div className="snapshot-bar__periods" role="group" aria-label="Период">
        {(Object.keys(PERIOD_LABELS) as Period[]).map((value) => (
          <Chip key={value} active={value === period} onClick={() => onPeriod(value)}>
            {PERIOD_LABELS[value]}
          </Chip>
        ))}
      </div>
      <div className="snapshot-bar__state">
        <span className="snapshot-bar__stamp" aria-live="polite">
          {recalc.isPending
            ? 'Идёт расчёт…'
            : snapshot
              ? `Данные на ${formatStamp(snapshot.computedAt)}`
              : 'Расчёта ещё не было'}
        </span>
        <Button
          size="inline"
          disabled={recalc.isPending || cooling}
          title={
            cooling && until
              ? `Повторный пересчёт — после ${formatStamp(until)}`
              : 'Посчитать заново по текущим данным'
          }
          onClick={() => recalc.mutate()}
        >
          {recalc.isPending ? 'Считаем…' : 'Пересчитать'}
        </Button>
        {exports.map((item) => (
          <ExportButton
            key={item.table}
            label={exports.length > 1 ? `CSV: ${item.label}` : 'Экспорт CSV'}
            path={`/admin/analytics/${block}/export.csv`}
            filename={`${block}-${item.table}-${period}.csv`}
            query={{ period, table: item.table, taskId }}
            disabled={!snapshot}
          />
        ))}
      </div>
      {cooling && until && !recalc.isPending && (
        <p className="admin-hint">
          Пересчёт этих данных доступен не чаще раза в 5 минут — снова после {formatStamp(until)}.
        </p>
      )}
      {recalc.isError && !retryAfter(recalc.error) && (
        <p className="admin-error" role="alert">
          {errorText(recalc.error)}
        </p>
      )}
    </div>
  )
}
