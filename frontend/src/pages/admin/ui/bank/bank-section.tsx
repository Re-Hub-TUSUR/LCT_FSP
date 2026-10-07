import { useState } from 'react'
import type { FormEvent } from 'react'
import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { Button, Chip, EmptyState, ErrorState, Loader, SelectField } from '@/shared/ui'
import { adminQueries } from '../../api/admin-api'
import type { BankFilters, TaskKind, TaskStatus } from '../../api/types'
import { errorText, formatDay, gradeLabel } from '../../lib/format'
import { KIND_LABELS, STATUS_LABELS } from '../../lib/labels'
import { useParam } from '../../lib/use-param'
import { ExportButton } from '../common/export-button'
import { Pager } from '../common/pager'
import { TaskDetails } from './task-details'
import { TaskEditor } from './task-editor'

export function BankSection() {
  const [taskId, setTaskId] = useParam('task')
  const [creating, setCreating] = useState(false)
  const [filters, setFilters] = useState<BankFilters>({ page: 1 })
  const [search, setSearch] = useState('')
  const list = useQuery({ ...adminQueries.bankList(filters), placeholderData: keepPreviousData })
  const dictionaries = useQuery(adminQueries.dictionaries())
  const skills = useQuery(adminQueries.skills())

  if (taskId) return <TaskDetails taskId={taskId} onBack={() => setTaskId(null)} />
  if (creating) {
    return (
      <section className="admin-section">
        <h1 className="admin-section__title">Новое задание</h1>
        <TaskEditor
          onDone={(created) => {
            setCreating(false)
            if (created) setTaskId(created)
          }}
        />
      </section>
    )
  }

  const set = (patch: Partial<BankFilters>) =>
    setFilters((prev) => ({ ...prev, page: 1, ...patch }))
  const grades = dictionaries.data?.grades ?? []
  const exportQuery = { ...filters, page: undefined }

  const submitSearch = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    set({ q: search.trim() || undefined })
  }

  return (
    <section className="admin-section">
      <header className="admin-section__head">
        <h1 className="admin-section__title">Банк заданий</h1>
        <div className="admin-section__actions">
          <ExportButton
            path="/admin/bank/tasks/export.csv"
            filename="task-bank.csv"
            query={exportQuery}
          />
          <Button size="inline" onClick={() => setCreating(true)}>
            Новое задание
          </Button>
        </div>
      </header>

      <div className="admin-filters">
        <form className="admin-search" role="search" onSubmit={submitSearch}>
          <input
            type="search"
            aria-label="Поиск по названию"
            placeholder="Поиск по названию"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
          <button type="submit">Найти</button>
        </form>
        <SelectField
          id="bank-specialization"
          label="Специализация"
          value={filters.specialization ?? ''}
          onChange={(event) => set({ specialization: event.target.value || undefined })}
        >
          <option value="">Все</option>
          {(dictionaries.data?.specializations ?? []).map((item) => (
            <option key={item.code} value={item.code}>
              {item.label}
            </option>
          ))}
        </SelectField>
        <SelectField
          id="bank-grade"
          label="Грейд"
          value={filters.grade ?? ''}
          onChange={(event) => set({ grade: event.target.value || undefined })}
        >
          <option value="">Все</option>
          {grades.map((grade) => (
            <option key={grade.code} value={grade.code}>
              {grade.label}
            </option>
          ))}
        </SelectField>
        <SelectField
          id="bank-skill"
          label="Навык"
          value={filters.skill ?? ''}
          onChange={(event) => set({ skill: event.target.value || undefined })}
        >
          <option value="">Все</option>
          {(skills.data ?? []).map((skill) => (
            <option key={skill} value={skill}>
              {skill}
            </option>
          ))}
        </SelectField>
      </div>
      <div className="admin-chips" role="group" aria-label="Тип и статус">
        <Chip active={!filters.kind} onClick={() => set({ kind: undefined })}>
          Все типы
        </Chip>
        {(Object.keys(KIND_LABELS) as TaskKind[]).map((kind) => (
          <Chip key={kind} active={filters.kind === kind} onClick={() => set({ kind })}>
            {KIND_LABELS[kind]}
          </Chip>
        ))}
        <span className="admin-chips__gap" />
        <Chip active={!filters.status} onClick={() => set({ status: undefined })}>
          Все статусы
        </Chip>
        {(Object.keys(STATUS_LABELS) as TaskStatus[]).map((status) => (
          <Chip key={status} active={filters.status === status} onClick={() => set({ status })}>
            {STATUS_LABELS[status]}
          </Chip>
        ))}
      </div>

      {list.isPending ? (
        <Loader />
      ) : list.isError ? (
        <ErrorState message={errorText(list.error)} onRetry={() => void list.refetch()} />
      ) : list.data.items.length === 0 ? (
        <EmptyState title="Заданий не найдено">
          Измените фильтры или добавьте новое задание.
        </EmptyState>
      ) : (
        <>
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
                  <th scope="col">Название</th>
                  <th scope="col">Тип</th>
                  <th scope="col">Специализации</th>
                  <th scope="col">Грейд</th>
                  <th scope="col">Навык</th>
                  <th scope="col">Статус</th>
                  <th scope="col">Изменено</th>
                </tr>
              </thead>
              <tbody>
                {list.data.items.map((task) => (
                  <tr key={task.id}>
                    <td>
                      <button
                        type="button"
                        className="admin-link"
                        onClick={() => setTaskId(task.id)}
                      >
                        {task.title}
                      </button>
                    </td>
                    <td>{KIND_LABELS[task.kind]}</td>
                    <td>{task.specializations.join(', ') || 'все'}</td>
                    <td>{gradeLabel(task.grade, grades)}</td>
                    <td>{task.skill}</td>
                    <td>
                      <span className={`status status--${task.status}`}>
                        {STATUS_LABELS[task.status]}
                      </span>
                    </td>
                    <td>{formatDay(task.updatedAt)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pager
            page={list.data.page}
            pages={list.data.pages}
            total={list.data.total}
            onPage={(page) => setFilters((prev) => ({ ...prev, page }))}
          />
        </>
      )}
    </section>
  )
}
