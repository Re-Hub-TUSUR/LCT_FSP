import { useState } from 'react'
import type { FormEvent } from 'react'
import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Button, EmptyState, ErrorState, Loader, SelectField, TextField } from '@/shared/ui'
import { adminApi, adminKeys, adminQueries } from '../../api/admin-api'
import type { Dictionaries, Parameter } from '../../api/types'
import { errorText, formatStamp } from '../../lib/format'
import { ExportButton } from '../common/export-button'
import { HistoryList } from '../common/history-list'
import { Pager } from '../common/pager'

function useDictionaryUpdate() {
  const queryClient = useQueryClient()
  return (data: Dictionaries) => {
    queryClient.setQueryData(adminKeys.dictionaries(), data)
    void queryClient.invalidateQueries({ queryKey: [...adminKeys.all, 'audit'] })
  }
}

function Specializations({ data }: { data: Dictionaries }) {
  const update = useDictionaryUpdate()
  const [code, setCode] = useState('')
  const [label, setLabel] = useState('')
  const [editing, setEditing] = useState<{ code: string; label: string } | null>(null)
  const add = useMutation({
    mutationFn: () => adminApi.addSpecialization(code.trim(), label.trim()),
    onSuccess: (d) => {
      update(d)
      setCode('')
      setLabel('')
    },
  })
  const change = useMutation({
    mutationFn: ({
      target,
      patch,
    }: {
      target: string
      patch: { label?: string; isArchived?: boolean }
    }) => adminApi.updateSpecialization(target, patch),
    onSuccess: (d) => {
      update(d)
      setEditing(null)
    },
  })
  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (code.trim() && label.trim()) add.mutate()
  }

  return (
    <article className="admin-card">
      <h2 className="admin-card__title">Специализации</h2>
      <ul className="dictionary">
        {data.specializations.map((item) => (
          <li key={item.code} className={item.isArchived ? 'is-muted' : undefined}>
            {editing?.code === item.code ? (
              <form
                className="dictionary__edit"
                onSubmit={(event) => {
                  event.preventDefault()
                  change.mutate({ target: item.code, patch: { label: editing.label } })
                }}
              >
                <input
                  aria-label="Название"
                  value={editing.label}
                  onChange={(e) => setEditing({ ...editing, label: e.target.value })}
                />
                <button type="submit" className="admin-link">
                  Сохранить
                </button>
                <button type="button" className="admin-link" onClick={() => setEditing(null)}>
                  Отмена
                </button>
              </form>
            ) : (
              <>
                <span>
                  {item.label} <code>{item.code}</code>
                  {!item.inPlatform && (
                    <span className="admin-sub">только в справочнике админки</span>
                  )}
                </span>
                <span className="dictionary__actions">
                  <button
                    type="button"
                    className="admin-link"
                    onClick={() => setEditing({ code: item.code, label: item.label })}
                  >
                    Переименовать
                  </button>
                  <button
                    type="button"
                    className="admin-link"
                    onClick={() =>
                      change.mutate({ target: item.code, patch: { isArchived: !item.isArchived } })
                    }
                  >
                    {item.isArchived ? 'Вернуть' : 'В архив'}
                  </button>
                </span>
              </>
            )}
          </li>
        ))}
      </ul>
      <form className="admin-form__row" onSubmit={submit}>
        <TextField
          id="spec-code"
          label="Код (латиница)"
          value={code}
          onChange={(e) => setCode(e.target.value)}
        />
        <TextField
          id="spec-label"
          label="Название"
          value={label}
          onChange={(e) => setLabel(e.target.value)}
        />
        <Button type="submit" size="inline" disabled={add.isPending}>
          Добавить
        </Button>
      </form>
      {(add.isError || change.isError) && (
        <p className="admin-error">{errorText(add.error ?? change.error)}</p>
      )}
    </article>
  )
}

function Skills({ data }: { data: Dictionaries }) {
  const update = useDictionaryUpdate()
  const [specialization, setSpecialization] = useState(data.specializations[0]?.code ?? '')
  const [name, setName] = useState('')
  const add = useMutation({
    mutationFn: () => adminApi.addSkill(specialization, name.trim()),
    onSuccess: (d) => {
      update(d)
      setName('')
    },
  })
  const toggle = useMutation({
    mutationFn: ({ id, isArchived }: { id: string; isArchived: boolean }) =>
      adminApi.updateSkill(id, { isArchived }),
    onSuccess: update,
  })
  const skills = data.skills.filter((skill) => skill.specializationCode === specialization)

  return (
    <article className="admin-card">
      <h2 className="admin-card__title">Навыки по специализациям</h2>
      <SelectField
        id="skill-spec"
        label="Специализация"
        value={specialization}
        onChange={(e) => setSpecialization(e.target.value)}
      >
        {data.specializations.map((item) => (
          <option key={item.code} value={item.code}>
            {item.label}
          </option>
        ))}
      </SelectField>
      {skills.length === 0 ? (
        <p className="admin-hint">Навыков пока нет.</p>
      ) : (
        <ul className="dictionary">
          {skills.map((skill) => (
            <li key={skill.id} className={skill.isArchived ? 'is-muted' : undefined}>
              <span>{skill.name}</span>
              <button
                type="button"
                className="admin-link"
                onClick={() => toggle.mutate({ id: skill.id, isArchived: !skill.isArchived })}
              >
                {skill.isArchived ? 'Вернуть' : 'В архив'}
              </button>
            </li>
          ))}
        </ul>
      )}
      <form
        className="admin-form__row"
        onSubmit={(event) => {
          event.preventDefault()
          if (name.trim() && specialization) add.mutate()
        }}
      >
        <TextField
          id="skill-name"
          label="Новый навык"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <Button type="submit" size="inline" disabled={add.isPending}>
          Добавить
        </Button>
      </form>
      {(add.isError || toggle.isError) && (
        <p className="admin-error">{errorText(add.error ?? toggle.error)}</p>
      )}
    </article>
  )
}

function ParameterRow({ item }: { item: Parameter }) {
  const queryClient = useQueryClient()
  const [value, setValue] = useState(String(item.value))
  const save = useMutation({
    mutationFn: () => adminApi.setParameter(item.key, Number(value)),
    onSuccess: (data) => {
      queryClient.setQueryData(adminKeys.parameters(), data)
      void queryClient.invalidateQueries({ queryKey: [...adminKeys.all, 'audit'] })
    },
  })
  const changed = value !== String(item.value)
  return (
    <tr>
      <td>
        {item.label}
        <span className="admin-sub">
          по умолчанию {item.default} {item.unit}
          {item.updatedAt && ` · изменён ${formatStamp(item.updatedAt)}`}
        </span>
      </td>
      <td>
        <form
          className="param"
          onSubmit={(event) => {
            event.preventDefault()
            if (changed) save.mutate()
          }}
        >
          <input
            aria-label={item.label}
            type="number"
            min={item.minimum}
            max={item.maximum}
            value={value}
            onChange={(event) => setValue(event.target.value)}
          />
          <span>{item.unit}</span>
          <button type="submit" className="admin-link" disabled={!changed || save.isPending}>
            Сохранить
          </button>
        </form>
        {save.isError && <span className="admin-error">{errorText(save.error)}</span>}
      </td>
    </tr>
  )
}

function Journal() {
  const [page, setPage] = useState(1)
  const [entity, setEntity] = useState<string | undefined>()
  const journal = useQuery({
    ...adminQueries.audit({ page, entity }),
    placeholderData: keepPreviousData,
  })
  return (
    <article className="admin-card">
      <header className="admin-section__head">
        <h2 className="admin-card__title">Журнал изменений</h2>
        <div className="admin-section__actions">
          <SelectField
            id="journal-entity"
            label="Что"
            hideLabel
            value={entity ?? ''}
            onChange={(e) => (setPage(1), setEntity(e.target.value || undefined))}
          >
            <option value="">Все изменения</option>
            <option value="parameter">Параметры</option>
            <option value="specialization">Специализации</option>
            <option value="skill">Навыки</option>
            <option value="task">Задания</option>
            <option value="company">Компании</option>
            <option value="banlist">Банлист</option>
            <option value="verification">Проверка компаний</option>
          </SelectField>
          <ExportButton
            path="/admin/audit/export.csv"
            filename="admin-journal.csv"
            query={{ entity }}
          />
        </div>
      </header>
      {journal.isPending ? (
        <Loader />
      ) : journal.isError ? (
        <ErrorState message={errorText(journal.error)} onRetry={() => void journal.refetch()} />
      ) : (
        <>
          <HistoryList entries={journal.data.items} withEntity />
          <Pager
            page={journal.data.page}
            pages={journal.data.pages}
            total={journal.data.total}
            onPage={setPage}
          />
        </>
      )}
    </article>
  )
}

export function SettingsSection() {
  const dictionaries = useQuery(adminQueries.dictionaries())
  const parameters = useQuery(adminQueries.parameters())

  return (
    <section className="admin-section">
      <header className="admin-section__head">
        <h1 className="admin-section__title">Справочники и параметры</h1>
      </header>
      {dictionaries.isPending ? (
        <Loader />
      ) : dictionaries.isError ? (
        <ErrorState
          message={errorText(dictionaries.error)}
          onRetry={() => void dictionaries.refetch()}
        />
      ) : (
        <>
          <div className="admin-columns">
            <Specializations data={dictionaries.data} />
            <Skills data={dictionaries.data} />
          </div>
          <article className="admin-card">
            <h2 className="admin-card__title">Грейды (11 уровней)</h2>
            <ol className="grades">
              {dictionaries.data.grades.map((grade) => (
                <li key={grade.code}>
                  <strong>{grade.label}</strong>
                  <span className="admin-sub">базовый уровень платформы: {grade.base}</span>
                </li>
              ))}
            </ol>
          </article>
        </>
      )}

      <article className="admin-card">
        <h2 className="admin-card__title">Параметры</h2>
        {parameters.isPending ? (
          <Loader />
        ) : parameters.isError ? (
          <ErrorState
            message={errorText(parameters.error)}
            onRetry={() => void parameters.refetch()}
          />
        ) : parameters.data.items.length === 0 ? (
          <EmptyState title="Параметров нет" />
        ) : (
          <>
            <div className="admin-table-wrap">
              <table className="admin-table">
                <tbody>
                  {parameters.data.items.map((item) => (
                    <ParameterRow key={`${item.key}:${item.value}`} item={item} />
                  ))}
                </tbody>
              </table>
            </div>
            <p className="admin-hint">
              Пороги флагов и сигналов применяются при следующем «Пересчитать». Эти значения код
              платформы пока берёт из своих мест, не отсюда:
            </p>
            <ul className="admin-list admin-hint">
              {parameters.data.hardcoded.map((item) => (
                <li key={item.parameter}>
                  <strong>{item.parameter}</strong>: <code>{item.where}</code>
                </li>
              ))}
            </ul>
          </>
        )}
      </article>
      <Journal />
    </section>
  )
}
