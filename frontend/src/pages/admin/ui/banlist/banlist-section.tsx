import { useState } from 'react'
import type { FormEvent } from 'react'
import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Button,
  Chip,
  EmptyState,
  ErrorState,
  Loader,
  Modal,
  TextArea,
  TextField,
} from '@/shared/ui'
import { adminApi, adminKeys, adminQueries } from '../../api/admin-api'
import type { BanCreate, BanEntry } from '../../api/types'
import { errorText, formatStamp } from '../../lib/format'
import { ExportButton } from '../common/export-button'
import { HistoryList } from '../common/history-list'
import { Pager } from '../common/pager'
import { ReasonDialog } from '../common/reason-dialog'

function AddBanDialog({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState<BanCreate>({ reason: '' })
  const add = useMutation({
    mutationFn: () => adminApi.addBan(form),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [...adminKeys.all, 'banlist'] })
      onClose()
    },
  })
  const set = (key: keyof BanCreate, value: string) =>
    setForm((prev) => ({ ...prev, [key]: value }))
  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    add.mutate()
  }

  return (
    <Modal title="Добавить в банлист" onClose={onClose}>
      <form className="admin-form" noValidate onSubmit={submit}>
        <TextField
          id="ban-company"
          label="Компания"
          value={form.companyName ?? ''}
          onChange={(e) => set('companyName', e.target.value)}
        />
        <TextField
          id="ban-inn"
          label="ИНН"
          inputMode="numeric"
          value={form.inn ?? ''}
          onChange={(e) => set('inn', e.target.value)}
        />
        <TextField
          id="ban-email"
          label="Email"
          type="email"
          value={form.email ?? ''}
          onChange={(e) => set('email', e.target.value)}
        />
        <TextField
          id="ban-domain"
          label="Домен почты"
          placeholder="example.ru"
          value={form.emailDomain ?? ''}
          onChange={(e) => set('emailDomain', e.target.value)}
        />
        <TextArea
          id="ban-reason"
          label="Причина (обязательно)"
          value={form.reason}
          onChange={(e) => set('reason', e.target.value)}
        />
        <p className="admin-hint">
          Нужно хотя бы одно: компания-клиент платформы, ИНН, email или домен.
        </p>
        {add.isError && (
          <p className="admin-error" role="alert">
            {errorText(add.error)}
          </p>
        )}
        <div className="admin-form__actions">
          <Button type="submit" size="inline" disabled={add.isPending}>
            {add.isPending ? 'Сохраняем…' : 'Заблокировать'}
          </Button>
          <Button variant="ghost" size="inline" onClick={onClose}>
            Отмена
          </Button>
        </div>
      </form>
    </Modal>
  )
}

function BanHistory({ ban, onClose }: { ban: BanEntry; onClose: () => void }) {
  const history = useQuery(adminQueries.banHistory(ban.id))
  return (
    <Modal
      title={`История: ${ban.companyName ?? ban.email ?? ban.emailDomain ?? ban.inn}`}
      onClose={onClose}
    >
      {history.isPending ? (
        <Loader />
      ) : history.isError ? (
        <ErrorState message={errorText(history.error)} />
      ) : (
        <HistoryList entries={history.data} />
      )}
    </Modal>
  )
}

export function BanlistSection() {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [q, setQ] = useState<string | undefined>()
  const [active, setActive] = useState<boolean | undefined>(true)
  const [adding, setAdding] = useState(false)
  const [unbanning, setUnbanning] = useState<BanEntry | null>(null)
  const [history, setHistory] = useState<BanEntry | null>(null)
  const list = useQuery({
    ...adminQueries.banlist({ page, q, active }),
    placeholderData: keepPreviousData,
  })
  const unban = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) => adminApi.unban(id, reason),
    onSuccess: () => {
      setUnbanning(null)
      void queryClient.invalidateQueries({ queryKey: [...adminKeys.all, 'banlist'] })
    },
  })

  return (
    <section className="admin-section">
      <header className="admin-section__head">
        <h1 className="admin-section__title">Банлист</h1>
        <div className="admin-section__actions">
          <ExportButton
            path="/admin/banlist/export.csv"
            filename="banlist.csv"
            query={{ q, active }}
          />
          <Button size="inline" onClick={() => setAdding(true)}>
            Добавить
          </Button>
        </div>
      </header>
      <div className="admin-filters">
        <form
          className="admin-search"
          role="search"
          onSubmit={(event) => {
            event.preventDefault()
            setPage(1)
            setQ(search.trim() || undefined)
          }}
        >
          <input
            type="search"
            aria-label="Поиск"
            placeholder="Компания, ИНН, email, домен, причина"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
          <button type="submit">Найти</button>
        </form>
        <div className="admin-chips" role="group" aria-label="Состояние">
          {(
            [
              [true, 'Действующие'],
              [false, 'Разблокированные'],
              [undefined, 'Все'],
            ] as const
          ).map(([value, label]) => (
            <Chip
              key={label}
              active={active === value}
              onClick={() => {
                setPage(1)
                setActive(value)
              }}
            >
              {label}
            </Chip>
          ))}
        </div>
      </div>

      {list.isPending ? (
        <Loader />
      ) : list.isError ? (
        <ErrorState message={errorText(list.error)} onRetry={() => void list.refetch()} />
      ) : list.data.items.length === 0 ? (
        <EmptyState title="Записей нет" />
      ) : (
        <>
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
                  <th scope="col">Компания</th>
                  <th scope="col">ИНН</th>
                  <th scope="col">Email</th>
                  <th scope="col">Домен</th>
                  <th scope="col">Причина</th>
                  <th scope="col">Дата и кто</th>
                  <th scope="col">Действия</th>
                </tr>
              </thead>
              <tbody>
                {list.data.items.map((ban) => (
                  <tr key={ban.id} className={ban.isActive ? undefined : 'is-muted'}>
                    <td>{ban.companyName ?? '—'}</td>
                    <td>{ban.inn ?? '—'}</td>
                    <td>{ban.email ?? '—'}</td>
                    <td>{ban.emailDomain ?? '—'}</td>
                    <td>
                      {ban.reason}
                      {!ban.isActive && (
                        <span className="admin-sub">
                          Разблокирован {ban.unbannedAt ? formatStamp(ban.unbannedAt) : ''}:{' '}
                          {ban.unbanReason}
                        </span>
                      )}
                    </td>
                    <td>
                      {formatStamp(ban.createdAt)}
                      <span className="admin-sub">{ban.createdByEmail ?? '—'}</span>
                    </td>
                    <td className="admin-table__actions">
                      {ban.isActive && (
                        <button
                          type="button"
                          className="admin-link"
                          onClick={() => setUnbanning(ban)}
                        >
                          Разблокировать
                        </button>
                      )}
                      <button type="button" className="admin-link" onClick={() => setHistory(ban)}>
                        История
                      </button>
                    </td>
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

      {adding && <AddBanDialog onClose={() => setAdding(false)} />}
      {history && <BanHistory ban={history} onClose={() => setHistory(null)} />}
      {unbanning && (
        <ReasonDialog
          title="Разблокировать"
          confirmLabel="Разблокировать"
          pending={unban.isPending}
          error={unban.isError ? errorText(unban.error) : null}
          onConfirm={(reason) => unban.mutate({ id: unbanning.id, reason })}
          onClose={() => setUnbanning(null)}
        />
      )}
    </section>
  )
}
