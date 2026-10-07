import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Button, ConfirmDialog, ErrorState, Loader } from '@/shared/ui'
import { adminApi, adminKeys, adminQueries } from '../../api/admin-api'
import type { CodePayload, QuizPayload, TaskStatus } from '../../api/types'
import { errorText, formatStamp, gradeLabel } from '../../lib/format'
import { DIFFICULTY_LABELS, KIND_LABELS, STATUS_LABELS } from '../../lib/labels'
import { HistoryList } from '../common/history-list'
import { ReasonDialog } from '../common/reason-dialog'
import { TaskEditor } from './task-editor'

const STATUS_ACTIONS: Record<TaskStatus, string> = {
  draft: 'В черновики',
  active: 'Сделать активным',
  leaked: 'Отметить как утёкшее',
  archived: 'В архив',
}

export function TaskDetails({ taskId, onBack }: { taskId: string; onBack: () => void }) {
  const queryClient = useQueryClient()
  const task = useQuery(adminQueries.task(taskId))
  const history = useQuery(adminQueries.taskHistory(taskId))
  const dictionaries = useQuery(adminQueries.dictionaries())
  const [editing, setEditing] = useState(false)
  const [target, setTarget] = useState<TaskStatus | null>(null)
  const [deleting, setDeleting] = useState(false)

  const refresh = () => {
    void queryClient.invalidateQueries({ queryKey: adminKeys.bank() })
    void queryClient.invalidateQueries({ queryKey: adminKeys.analytics() })
  }
  const move = useMutation({
    mutationFn: ({ status, reason }: { status: TaskStatus; reason?: string }) =>
      adminApi.setTaskStatus(taskId, status, reason),
    onSuccess: () => {
      setTarget(null)
      refresh()
    },
  })
  const remove = useMutation({
    mutationFn: () => adminApi.deleteTask(taskId),
    onSuccess: () => {
      refresh()
      onBack()
    },
  })

  if (task.isPending) return <Loader />
  if (task.isError) {
    return (
      <section className="admin-section">
        <Button variant="ghost" size="inline" onClick={onBack}>
          ← К списку
        </Button>
        <ErrorState message={errorText(task.error)} onRetry={() => void task.refetch()} />
      </section>
    )
  }
  const data = task.data

  if (editing) {
    return (
      <section className="admin-section">
        <h1 className="admin-section__title">Редактирование: {data.title}</h1>
        <TaskEditor
          task={data}
          onDone={() => {
            setEditing(false)
            refresh()
          }}
        />
      </section>
    )
  }

  return (
    <section className="admin-section">
      <Button variant="ghost" size="inline" onClick={onBack}>
        ← К списку
      </Button>
      <header className="admin-section__head">
        <div>
          <h1 className="admin-section__title">{data.title}</h1>
          <p className="admin-meta">
            <span className={`status status--${data.status}`}>{STATUS_LABELS[data.status]}</span>
            <span>{KIND_LABELS[data.kind]}</span>
            <span>Грейд: {gradeLabel(data.grade, dictionaries.data?.grades ?? [])}</span>
            <span>Навык: {data.skill}</span>
            <span>Сложность: {DIFFICULTY_LABELS[data.difficulty]}</span>
            <span>
              Лимит: {data.timeLimitMinutes ? `${data.timeLimitMinutes} мин` : 'по тесту'}
            </span>
            <span>Попыток с заданием: {data.attempts}</span>
          </p>
        </div>
        <div className="admin-section__actions">
          <Button variant="ghost" size="inline" onClick={() => setEditing(true)}>
            Редактировать
          </Button>
          {data.allowedStatuses.map((status) => (
            <Button
              key={status}
              variant={status === 'active' ? 'solid' : 'ghost'}
              size="inline"
              disabled={move.isPending}
              onClick={() => (status === 'active' ? move.mutate({ status }) : setTarget(status))}
            >
              {STATUS_ACTIONS[status]}
            </Button>
          ))}
          {data.canDelete && (
            <Button variant="ghost" size="inline" onClick={() => setDeleting(true)}>
              Удалить
            </Button>
          )}
        </div>
      </header>
      {move.isError && !target && <p className="admin-error">{errorText(move.error)}</p>}
      {!data.canDelete && data.status === 'draft' && (
        <p className="admin-hint">
          Задание уже было в попытках кандидатов: удалить нельзя, только архивировать.
        </p>
      )}

      <div className="admin-columns">
        <article className="admin-card">
          <h2 className="admin-card__title">Условие</h2>
          <p className="admin-pre">{data.statement}</p>
          {data.variables.length > 0 && (
            <p className="admin-hint">
              Переменные:{' '}
              {data.variables
                .map((v) => `${v.name} ∈ [${v.min}; ${v.max}], шаг ${v.step}`)
                .join(' · ')}
            </p>
          )}
          {data.kind === 'quiz' ? (
            <ul className="admin-list">
              {(data.payload as QuizPayload).options.map((option, index) => (
                <li key={index}>
                  {(data.payload as QuizPayload).correct.includes(index) ? '✓ ' : '· '}
                  {option}
                </li>
              ))}
            </ul>
          ) : (
            <ul className="admin-list">
              {(data.payload as CodePayload).groups.map((group, index) => (
                <li key={index}>
                  {group.hidden ? 'Скрытый' : 'Открытый'}: <code>{group.input || '∅'}</code> →{' '}
                  <code>{group.expected}</code>
                </li>
              ))}
            </ul>
          )}
          <p className="admin-hint">Создано {formatStamp(data.createdAt)}</p>
        </article>
        <article className="admin-card">
          <h2 className="admin-card__title">История изменений</h2>
          {history.isPending ? (
            <Loader />
          ) : history.isError ? (
            <ErrorState message={errorText(history.error)} />
          ) : (
            <HistoryList entries={history.data.items} />
          )}
        </article>
      </div>

      {target && (
        <ReasonDialog
          title={`${STATUS_ACTIONS[target]}: «${data.title}»`}
          confirmLabel={STATUS_ACTIONS[target]}
          required={target === 'leaked'}
          label={target === 'leaked' ? 'Где нашли утечку' : 'Комментарий'}
          pending={move.isPending}
          error={move.isError ? errorText(move.error) : null}
          onConfirm={(reason) => move.mutate({ status: target, reason: reason || undefined })}
          onClose={() => setTarget(null)}
        >
          <p className="admin-hint">
            {target === 'leaked' || target === 'archived'
              ? 'Задание перестанет выдаваться кандидатам. Уже начатые попытки не изменятся.'
              : null}
          </p>
        </ReasonDialog>
      )}
      {deleting && (
        <ConfirmDialog
          title="Удалить черновик?"
          confirmLabel="Удалить"
          busy={remove.isPending}
          onConfirm={() => remove.mutate()}
          onCancel={() => setDeleting(false)}
        >
          «{data.title}» будет удалено без возможности восстановления.
        </ConfirmDialog>
      )}
      {remove.isError && <p className="admin-error">{errorText(remove.error)}</p>}
    </section>
  )
}
