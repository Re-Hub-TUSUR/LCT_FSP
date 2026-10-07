import { useState } from 'react'
import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Button, Chip, EmptyState, ErrorState, Loader } from '@/shared/ui'
import { adminApi, adminKeys, adminQueries } from '../../api/admin-api'
import type { CompanyDocument, VerificationStatus } from '../../api/types'
import { openPdf, saveBlob } from '../../lib/download'
import { errorText, formatBytes, formatStamp } from '../../lib/format'
import { VERIFICATION_LABELS } from '../../lib/labels'
import { useParam } from '../../lib/use-param'
import { ExportButton } from '../common/export-button'
import { HistoryList } from '../common/history-list'
import { Pager } from '../common/pager'
import { ReasonDialog } from '../common/reason-dialog'

function RequestCard({ companyId, onBack }: { companyId: string; onBack: () => void }) {
  const queryClient = useQueryClient()
  const detail = useQuery(adminQueries.verification(companyId))
  const [decision, setDecision] = useState<'approve' | 'reject' | null>(null)
  const [opening, setOpening] = useState<string | null>(null)
  const [openError, setOpenError] = useState<string | null>(null)
  const decide = useMutation({
    mutationFn: ({ approve, reason }: { approve: boolean; reason: string }) =>
      approve
        ? adminApi.approve(companyId, reason || undefined)
        : adminApi.reject(companyId, reason),
    onSuccess: (data) => {
      setDecision(null)
      queryClient.setQueryData(adminKeys.verification(companyId), data)
      void queryClient.invalidateQueries({ queryKey: [...adminKeys.all, 'verifications'] })
    },
  })

  const open = async (file: CompanyDocument) => {
    setOpening(file.id)
    setOpenError(null)
    try {
      const blob = await adminApi.documentBlob(companyId, file.id)
      if (file.kind === 'docx') saveBlob(blob, file.filename)
      else openPdf(blob)
    } catch (cause) {
      setOpenError(errorText(cause))
    } finally {
      setOpening(null)
    }
  }

  if (detail.isPending) return <Loader />
  if (detail.isError) {
    return (
      <section className="admin-section">
        <Button variant="ghost" size="inline" onClick={onBack}>
          ← К заявкам
        </Button>
        <ErrorState message={errorText(detail.error)} onRetry={() => void detail.refetch()} />
      </section>
    )
  }
  const data = detail.data

  return (
    <section className="admin-section">
      <Button variant="ghost" size="inline" onClick={onBack}>
        ← К заявкам
      </Button>
      <header className="admin-section__head">
        <div>
          <h1 className="admin-section__title">{data.companyName}</h1>
          <p className="admin-meta">
            <span className={`verification verification--${data.status}`}>
              {VERIFICATION_LABELS[data.status]}
            </span>
            <span>Подана {formatStamp(data.submittedAt)}</span>
            {data.decidedAt && (
              <span>
                Решение {formatStamp(data.decidedAt)} · {data.decidedByEmail ?? '—'}
              </span>
            )}
          </p>
        </div>
        <div className="admin-section__actions">
          {data.status !== 'approved' && (
            <Button size="inline" onClick={() => setDecision('approve')}>
              Согласовать
            </Button>
          )}
          {data.status !== 'rejected' && (
            <Button variant="ghost" size="inline" onClick={() => setDecision('reject')}>
              Отклонить
            </Button>
          )}
        </div>
      </header>
      {data.decisionReason && (
        <p className="admin-hint">Комментарий к решению: {data.decisionReason}</p>
      )}

      <div className="admin-columns">
        <article className="admin-card">
          <h2 className="admin-card__title">Выписка Минцифры ({data.files.length})</h2>
          {data.files.length === 0 ? (
            <p className="admin-hint">Компания удалила все файлы.</p>
          ) : (
            <ul className="documents">
              {data.files.map((file) => (
                <li key={file.id}>
                  <button
                    type="button"
                    className="admin-link"
                    disabled={opening === file.id}
                    onClick={() => void open(file)}
                  >
                    {file.filename}
                  </button>
                  <span className="admin-sub">
                    {file.kind === 'docx' ? 'DOCX, скачается' : 'PDF'} ·{' '}
                    {formatBytes(file.sizeBytes)} · {formatStamp(file.uploadedAt)}
                  </span>
                </li>
              ))}
            </ul>
          )}
          {openError && <p className="admin-error">{openError}</p>}
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
          </dl>
        </article>
        <article className="admin-card">
          <h2 className="admin-card__title">История</h2>
          <HistoryList entries={data.history} />
        </article>
      </div>

      {decision && (
        <ReasonDialog
          title={decision === 'approve' ? 'Подтвердить IT-аккредитацию' : 'Отклонить выписку'}
          confirmLabel={decision === 'approve' ? 'Согласовать' : 'Отклонить'}
          required={decision === 'reject'}
          label={decision === 'approve' ? 'Комментарий' : 'Причина (её увидит компания)'}
          pending={decide.isPending}
          error={decide.isError ? errorText(decide.error) : null}
          onConfirm={(reason) => decide.mutate({ approve: decision === 'approve', reason })}
          onClose={() => setDecision(null)}
        />
      )}
    </section>
  )
}

export function VerificationSection() {
  const [companyId, setCompanyId] = useParam('company')
  const [status, setStatus] = useState<VerificationStatus | undefined>('pending')
  const [page, setPage] = useState(1)
  const list = useQuery({
    ...adminQueries.verifications({ page, status }),
    placeholderData: keepPreviousData,
  })

  if (companyId) return <RequestCard companyId={companyId} onBack={() => setCompanyId(null)} />

  return (
    <section className="admin-section">
      <header className="admin-section__head">
        <h1 className="admin-section__title">IT-аккредитация компаний</h1>
        <div className="admin-section__actions">
          <ExportButton
            path="/admin/verifications/export.csv"
            filename="company-verification.csv"
            query={{ status }}
          />
        </div>
      </header>
      <p className="admin-hint">
        Компания загружает выписку из реестра аккредитованных IT-компаний Минцифры (PDF или DOCX).
        Сверьте название и ИНН с профилем и согласуйте или отклоните заявку. После согласования у
        компании появится отметка в ленте, причину отказа компания увидит.
      </p>
      <div className="admin-chips" role="group" aria-label="Статус">
        {([undefined, 'pending', 'approved', 'rejected'] as const).map((value) => (
          <Chip
            key={value ?? 'all'}
            active={status === value}
            onClick={() => {
              setPage(1)
              setStatus(value)
            }}
          >
            {value ? VERIFICATION_LABELS[value] : 'Все'}
          </Chip>
        ))}
      </div>
      {list.isPending ? (
        <Loader />
      ) : list.isError ? (
        <ErrorState message={errorText(list.error)} onRetry={() => void list.refetch()} />
      ) : list.data.items.length === 0 ? (
        <EmptyState title={status === 'pending' ? 'Новых заявок нет' : 'Заявок нет'} />
      ) : (
        <>
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
                  <th scope="col">Компания</th>
                  <th scope="col">Владелец</th>
                  <th scope="col">Статус</th>
                  <th scope="col">Подана</th>
                  <th scope="col">Документов</th>
                </tr>
              </thead>
              <tbody>
                {list.data.items.map((row) => (
                  <tr key={row.companyId}>
                    <td>
                      <button
                        type="button"
                        className="admin-link"
                        onClick={() => setCompanyId(row.companyId)}
                      >
                        {row.companyName}
                      </button>
                    </td>
                    <td>{row.ownerEmail}</td>
                    <td>
                      <span className={`verification verification--${row.status}`}>
                        {VERIFICATION_LABELS[row.status]}
                      </span>
                    </td>
                    <td>{formatStamp(row.submittedAt)}</td>
                    <td>{row.documents}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pager
            page={list.data.page}
            pages={list.data.pages}
            total={list.data.total}
            onPage={setPage}
          />
        </>
      )}
    </section>
  )
}
