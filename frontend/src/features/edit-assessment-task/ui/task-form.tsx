import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { DIFFICULTY_LABELS, bankApi, bankKeys } from '@/entities/assessment'
import type { BankScope, BankTaskDto, TaskDifficulty, TaskKind } from '@/entities/assessment'
import { categoryQueries } from '@/entities/category'
import { getErrorMessage } from '@/shared/api'
import { Button, Chip, SelectField, TextArea, TextField } from '@/shared/ui'
import { toFormValues, toPayload, validateTask } from '../model/form'
import type { TaskFormValues } from '../model/form'
import { KIND_EDITORS } from '../model/kinds'
import { CodeFields } from './kind-fields/code-fields'
import { OpenFields } from './kind-fields/open-fields'
import { QuizFields } from './kind-fields/quiz-fields'
import './task-form.css'

type Props = {
  scope: BankScope
  kind: TaskKind
  /** Present when an existing task is edited. */
  task?: BankTaskDto
  onDone: () => void
}

const toggle = <T,>(list: T[], item: T) =>
  list.includes(item) ? list.filter((value) => value !== item) : [...list, item]

/**
 * One form for both authors: admins fill the platform bank, employers — their own.
 * The common fields are here; the content of each kind is edited by its own fields component.
 */
export function TaskForm({ scope, kind, task, onDone }: Props) {
  const queryClient = useQueryClient()
  const dictionary = useQuery(categoryQueries.dictionary())
  const [values, setValues] = useState<TaskFormValues>(() => toFormValues(kind, task))
  const [problem, setProblem] = useState<string | null>(null)
  const editor = KIND_EDITORS[kind]

  const save = useMutation({
    mutationFn: () => bankApi.saveTask(scope, toPayload(values), task?.id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: bankKeys.tasks(scope) })
      onDone()
    },
  })

  const set = <K extends keyof TaskFormValues>(key: K, value: TaskFormValues[K]) => {
    setValues((prev) => ({ ...prev, [key]: value }))
    setProblem(null)
  }

  const onSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const found = validateTask(values)
    setProblem(found)
    if (!found) save.mutate()
  }

  return (
    <form className="task-form" noValidate onSubmit={onSubmit}>
      <h3 className="task-form__heading">
        {task ? 'Редактирование' : 'Новая запись'}: {editor.label}
      </h3>

      {editor.titled && (
        <TextField
          id="task-title"
          label="Название"
          value={values.title}
          maxLength={200}
          onChange={(e) => set('title', e.target.value)}
        />
      )}
      <TextArea
        id="task-statement"
        label={editor.statementLabel}
        value={values.statement}
        onChange={(e) => set('statement', e.target.value)}
      />

      <div className="task-form__row">
        <TextField
          id="task-topic"
          label="Тема (код, например sql)"
          value={values.topic}
          maxLength={64}
          onChange={(e) => set('topic', e.target.value)}
        />
        <SelectField
          id="task-difficulty"
          label="Сложность"
          value={values.difficulty}
          onChange={(e) => set('difficulty', e.target.value as TaskDifficulty)}
        >
          {Object.entries(DIFFICULTY_LABELS).map(([code, label]) => (
            <option key={code} value={code}>
              {label}
            </option>
          ))}
        </SelectField>
      </div>

      <fieldset className="task-form__group">
        <legend>Специализации (ничего не выбрано — подходит всем)</legend>
        <div className="task-form__chips">
          {(dictionary.data?.specializations ?? []).map((item) => (
            <Chip
              key={item.code}
              active={values.specializations.includes(item.code)}
              onClick={() => set('specializations', toggle(values.specializations, item.code))}
            >
              {item.label}
            </Chip>
          ))}
        </div>
      </fieldset>

      {kind === 'quiz' && (
        <QuizFields draft={values.quiz} onChange={(draft) => set('quiz', draft)} />
      )}
      {kind === 'code' && (
        <CodeFields draft={values.code} onChange={(draft) => set('code', draft)} />
      )}
      {kind === 'open' && (
        <OpenFields draft={values.open} onChange={(draft) => set('open', draft)} />
      )}

      <label className="task-form__check">
        <input
          type="checkbox"
          checked={values.isActive}
          onChange={(e) => set('isActive', e.target.checked)}
        />
        <span>Активна: может попадать в тесты</span>
      </label>

      {(problem || save.isError) && (
        <p className="task-form__error" role="alert">
          {problem ?? getErrorMessage(save.error)}
        </p>
      )}

      <div className="task-form__actions">
        <Button type="submit" size="inline" disabled={save.isPending}>
          {save.isPending ? 'Сохраняем…' : 'Сохранить'}
        </Button>
        <Button variant="ghost" size="inline" disabled={save.isPending} onClick={onDone}>
          Отмена
        </Button>
      </div>
    </form>
  )
}
