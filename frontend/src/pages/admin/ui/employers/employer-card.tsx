import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Button, ErrorState, Loader, TextField } from '@/shared/ui'
import { adminApi, adminKeys, adminQueries } from '../../api/admin-api'
import type { EmployerAction, Period } from '../../api/types'
import { errorText, formatDay, formatPercent, formatStamp } from '../../lib/format'
import {
  ACTION_LABELS,
  CASE_LABELS,
  OUTREACH_LABELS,
  SIGNAL_LABELS,
  VERIFICATION_LABELS,
} from '../../lib/labels'
import { HistoryList } from '../common/history-list'
import { ReasonDialog } from '../common/reason-dialog'

type Props = { companyId: string; period: Period; onBack: () => void }

export function EmployerCardView({ companyId, period, onBack }: Props) {
  const queryClient = useQueryClient()
  const card = useQuery(adminQueries.employer(companyId, period))
  const [action, setAction] = useState<EmployerAction | null>(null)
  const [limit, setLimit] = useState('5')
  const decide = useMutation({
    mutationFn: ({ chosen, reason }: { chosen: EmployerAction; reason: string }) =>
      adminApi.decide(companyId, chosen, reason, chosen === 'restrict' ? Number(limit) : undefined),
    onSuccess: (updated) => {
      setAction(null)
      queryClient.setQueryData(adminKeys.employer(companyId, period), updated)
      void queryClient.invalidateQueries({ queryKey: adminKeys.analytics() })
      void queryClient.invalidateQueries({ queryKey: [...adminKeys.all, 'banlist'] })
    },
  })

  if (card.isPending) return <Loader />
  if (card.isError) {
    return (
      <section className="admin-section">
        <Button variant="ghost" size="inline" onClick={onBack}>
          ← К списку
        </Button>
        <ErrorState message={errorText(card.error)} onRetry={() => void card.refetch()} />
      </section>
    )
  }
  const data = card.data
  const signals = data.signals

  return (
    <section className="admin-section">
      <Button variant="ghost" size="inline" onClick={onBack}>
        ← К списку
      </Button>
      <header className="admin-section__head">
        <div>
          <h1 className="admin-section__title">{data.name}</h1>
          <p className="admin-meta">
            <span>{data.case ? CASE_LABELS[data.case.status] : 'Решений не было'}</span>
            {data.case?.inviteLimit != null && (
              <span>Лимит: {data.case.inviteLimit} приглашений в сутки</span>
            )}
            <span>
              Документы:{' '}
              {data.verification ? VERIFICATION_LABELS[data.verification] : 'не загружены'}
            </span>
            {data.banned && <span className="flag flag--possible_leak">В банлисте</span>}
          </p>
        </div>
        <div className="admin-section__actions">
          {(Object.keys(ACTION_LABELS) as EmployerAction[]).map((code) => (
            <Button
              key={code}
              variant={code === 'block' ? 'solid' : 'ghost'}
              size="inline"
              onClick={() => setAction(code)}
            >
              {ACTION_LABELS[code]}
            </Button>
          ))}
        </div>
      </header>

      <div className="admin-columns">
        <article className="admin-card">
          <h2 className="admin-card__title">Сигналы</h2>
          {data.liveSignals.length > 0 && (
            <ul className="admin-list">
              {data.liveSignals.map((signal) => (
                <li key={signal.code}>
                  {SIGNAL_LABELS[signal.code] ?? signal.code}: {signal.hits},{' '}
                  {formatStamp(signal.lastAt)}
                </li>
              ))}
            </ul>
          )}
          {!signals && data.liveSignals.length === 0 ? (
            <p className="admin-hint">
              {data.snapshot
                ? `В расчёте от ${formatStamp(data.snapshot.computedAt)} активности компании не было.`
                : 'Сигналы ещё не считались: нажмите «Пересчитать» в списке.'}
            </p>
          ) : signals ? (
            <dl className="admin-dl">
              <dt>Сигналы</dt>
              <dd>
                {signals.signals.length
                  ? signals.signals.map((s) => SIGNAL_LABELS[s] ?? s).join('; ')
                  : 'нет'}
              </dd>
              <dt>Приглашений за период</dt>
              <dd>{signals.invitesTotal}</dd>
              <dt>Пик за сутки / медиана работодателей</dt>
              <dd>
                {signals.invitesMaxPerDay} / {signals.invitesMedianPerDay ?? '—'}
              </dd>
              <dt>Отклики кандидатов / ответы компании</dt>
              <dd>
                {signals.inbound} / {signals.answered} ({formatPercent(signals.responseShare)})
              </dd>
              <dt>Вакансии, закрытые без найма</dt>
              <dd>нет данных: у вакансий нет статуса закрытия</dd>
              <dt>Жалобы кандидатов</dt>
              <dd>нет данных: жалоб в платформе нет</dd>
            </dl>
          ) : null}
          <h2 className="admin-card__title">Компания</h2>
          <dl className="admin-dl">
            <dt>Владелец</dt>
            <dd>{data.ownerEmail}</dd>
            <dt>Контакт</dt>
            <dd>{data.contactEmail ?? '—'}</dd>
            <dt>Сайт</dt>
            <dd>{data.website ?? '—'}</dd>
            <dt>Отрасль, город</dt>
            <dd>{[data.industry, data.city].filter(Boolean).join(', ') || '—'}</dd>
            <dt>Регистрация</dt>
            <dd>{formatDay(data.registeredAt)}</dd>
          </dl>
        </article>
        <article className="admin-card">
          <h2 className="admin-card__title">История решений</h2>
          <HistoryList entries={data.history} />
        </article>
      </div>

      <h2 className="admin-card__title">Вакансии ({data.vacancies.length})</h2>
      {data.vacancies.length === 0 ? (
        <p className="admin-hint">Вакансий нет.</p>
      ) : (
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th scope="col">Вакансия</th>
                <th scope="col">Категория</th>
                <th scope="col">Создана</th>
                <th scope="col">Опубликована</th>
              </tr>
            </thead>
            <tbody>
              {data.vacancies.map((vacancy) => (
                <tr key={vacancy.id}>
                  <td>{vacancy.title}</td>
                  <td>
                    {vacancy.specialization} · {vacancy.grade}
                  </td>
                  <td>{formatDay(vacancy.createdAt)}</td>
                  <td>{vacancy.publishedAt ? formatDay(vacancy.publishedAt) : 'черновик'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <h2 className="admin-card__title">Приглашения и обращения к кандидатам</h2>
      {data.outreach.length === 0 ? (
        <p className="admin-hint">Обращений нет.</p>
      ) : (
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th scope="col">Когда</th>
                <th scope="col">Тип</th>
                <th scope="col">Кандидат</th>
                <th scope="col">Статус</th>
              </tr>
            </thead>
            <tbody>
              {data.outreach.map((item, index) => (
                <tr key={`${item.candidateId}-${item.createdAt}-${index}`}>
                  <td>{formatStamp(item.createdAt)}</td>
                  <td>{OUTREACH_LABELS[item.kind]}</td>
                  <td>{item.candidateName}</td>
                  <td>{item.status ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {action && (
        <ReasonDialog
          title={`${ACTION_LABELS[action]}: ${data.name}`}
          confirmLabel={ACTION_LABELS[action]}
          pending={decide.isPending}
          error={decide.isError ? errorText(decide.error) : null}
          onConfirm={(reason) => decide.mutate({ chosen: action, reason })}
          onClose={() => setAction(null)}
        >
          {action === 'restrict' && (
            <TextField
              id="invite-limit"
              label="Лимит приглашений в сутки"
              inputMode="numeric"
              value={limit}
              onChange={(event) => setLimit(event.target.value)}
            />
          )}
          {action === 'block' && (
            <p className="admin-hint">Компания и email владельца попадут в банлист.</p>
          )}
        </ReasonDialog>
      )}
    </section>
  )
}
