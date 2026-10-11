import { useState } from 'react'
import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { Chip, EmptyState, ErrorState, Loader } from '@/shared/ui'
import { adminQueries } from '../../api/admin-api'
import type { CaseStatus, Period } from '../../api/types'
import { errorText, formatPercent } from '../../lib/format'
import { CASE_LABELS, SIGNAL_LABELS } from '../../lib/labels'
import { useParam } from '../../lib/use-param'
import { Pager } from '../common/pager'
import { SnapshotBar } from '../common/snapshot-bar'
import { EmployerCardView } from './employer-card'

export function EmployersSection() {
  const [companyId, setCompanyId] = useParam('company')
  const [period, setPeriod] = useState<Period>('90d')
  const [page, setPage] = useState(1)
  const [signal, setSignal] = useState<string | undefined>('any')
  const [status, setStatus] = useState<CaseStatus | undefined>()
  const table = useQuery({
    ...adminQueries.employerTable({ period, page, signal, status }),
    placeholderData: keepPreviousData,
  })

  if (companyId) {
    return (
      <EmployerCardView companyId={companyId} period={period} onBack={() => setCompanyId(null)} />
    )
  }
  const summary = table.data?.summary

  return (
    <section className="admin-section">
      <header className="admin-section__head">
        <h1 className="admin-section__title">Работодатели под подозрением</h1>
      </header>
      <SnapshotBar
        block="employers"
        period={period}
        onPeriod={(value) => {
          setPage(1)
          setPeriod(value)
        }}
        snapshot={table.data?.snapshot}
        exports={[{ table: 'companies', label: 'компании' }]}
      />
      {summary && (
        <div className="tiles">
          <div className="tile">
            <span className="tile__value">{summary.flagged}</span>
            <span className="tile__label">с сигналами из {summary.companies} активных</span>
          </div>
          <div className="tile tile--flag">
            <span className="tile__value">{summary.invitesSpike}</span>
            <span className="tile__label">{SIGNAL_LABELS.invites_spike}</span>
          </div>
          <div className="tile tile--flag">
            <span className="tile__value">{summary.lowResponse}</span>
            <span className="tile__label">{SIGNAL_LABELS.low_response}</span>
          </div>
          <div className="tile">
            <span className="tile__value">{summary.medianInvitesPerDay ?? '—'}</span>
            <span className="tile__label">медиана приглашений за сутки (пиковый день)</span>
          </div>
        </div>
      )}
      <div className="admin-chips" role="group" aria-label="Фильтр">
        <Chip
          active={signal === 'any'}
          onClick={() => {
            setPage(1)
            setSignal('any')
          }}
        >
          С сигналами
        </Chip>
        <Chip
          active={signal === undefined}
          onClick={() => {
            setPage(1)
            setSignal(undefined)
          }}
        >
          Все активные
        </Chip>
        <span className="admin-chips__gap" />
        <Chip
          active={!status}
          onClick={() => {
            setPage(1)
            setStatus(undefined)
          }}
        >
          Любое решение
        </Chip>
        {(Object.keys(CASE_LABELS) as CaseStatus[]).map((code) => (
          <Chip
            key={code}
            active={status === code}
            onClick={() => {
              setPage(1)
              setStatus(code)
            }}
          >
            {CASE_LABELS[code]}
          </Chip>
        ))}
      </div>
      {(table.data?.unavailable ?? []).length > 0 && (
        <ul className="admin-list admin-hint">
          {table.data?.unavailable.map((item) => (
            <li key={item}>Нет данных — {item}</li>
          ))}
        </ul>
      )}

      {table.isPending ? (
        <Loader />
      ) : table.isError ? (
        <ErrorState message={errorText(table.error)} onRetry={() => void table.refetch()} />
      ) : !table.data.snapshot && table.data.items.length === 0 ? (
        <EmptyState title="Данных пока нет">Нажмите «Пересчитать».</EmptyState>
      ) : table.data.items.length === 0 ? (
        <EmptyState title="Подозрительных компаний нет" />
      ) : (
        <>
          <div className="admin-table-wrap">
            <table className="admin-table admin-table--numbers">
              <thead>
                <tr>
                  <th scope="col">Компания</th>
                  <th scope="col">Сигналы</th>
                  <th scope="col">Приглашений</th>
                  <th scope="col">Пик за сутки</th>
                  <th scope="col">Отклики / ответы</th>
                  <th scope="col">Доля ответов</th>
                  <th scope="col">Решение</th>
                </tr>
              </thead>
              <tbody>
                {table.data.items.map((row) => (
                  <tr key={row.companyId}>
                    <td>
                      <button
                        type="button"
                        className="admin-link"
                        onClick={() => setCompanyId(row.companyId)}
                      >
                        {row.name}
                      </button>
                    </td>
                    <td>
                      {row.signals.length === 0
                        ? '—'
                        : row.signals.map((code) => (
                            <span key={code} className="flag flag--possible_leak">
                              {SIGNAL_LABELS[code] ?? code}
                            </span>
                          ))}
                    </td>
                    <td>{row.invitesTotal}</td>
                    <td>{row.invitesMaxPerDay}</td>
                    <td>
                      {row.inbound} / {row.answered}
                    </td>
                    <td>{formatPercent(row.responseShare)}</td>
                    <td>{row.caseStatus ? CASE_LABELS[row.caseStatus] : '—'}</td>
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
