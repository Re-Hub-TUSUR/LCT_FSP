import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { DIFFICULTY_LABELS, LANGUAGES, bankApi, bankKeys } from '@/entities/assessment'
import type { BankScope, BankTaskDto, TaskDifficulty, TaskKind } from '@/entities/assessment'
import { categoryQueries } from '@/entities/category'
import { getErrorMessage } from '@/shared/api'
import { Button, Chip, CodeEditor, SelectField, TextArea, TextField } from '@/shared/ui'
import { MAX_EXPECTED_OUTPUT, toFormValues, toPayload, validateTask } from '../model/form'
import type { TaskFormValues } from '../model/form'
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

/** One form for both authors: admins fill the platform bank, employers — their own. */
export function TaskForm({ scope, kind, task, onDone }: Props) {
  const queryClient = useQueryClient()
  const dictionary = useQuery(categoryQueries.dictionary())
  const [values, setValues] = useState<TaskFormValues>(() => toFormValues(kind, task))
  const [problem, setProblem] = useState<string | null>(null)

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

  const setOption = (index: number, text: string) =>
    set(
      'options',
      values.options.map((option, position) => (position === index ? text : option)),
    )

  const removeOption = (index: number) => {
    setValues((prev) => ({
      ...prev,
      options: prev.options.filter((_, position) => position !== index),
      // Indexes after the removed option shift down by one.
      correct: prev.correct
        .filter((position) => position !== index)
        .map((position) => (position > index ? position - 1 : position)),
    }))
  }

  const markCorrect = (index: number) =>
    set('correct', values.multiple ? toggle(values.correct, index) : [index])

  const setGroup = (index: number, patch: Partial<TaskFormValues['groups'][number]>) =>
    set(
      'groups',
      values.groups.map((group, position) => (position === index ? { ...group, ...patch } : group)),
    )

  return (
    <form className="task-form" noValidate onSubmit={onSubmit}>
      <h3 className="task-form__heading">
        {task ? 'Редактирование' : 'Новая запись'}: {kind === 'quiz' ? 'вопрос' : 'задача на код'}
      </h3>

      {kind === 'code' && (
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
        label={kind === 'quiz' ? 'Вопрос' : 'Условие: формат ввода и вывода'}
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

      {kind === 'quiz' ? (
        <fieldset className="task-form__group">
          <legend>Варианты ответа — отметьте верный</legend>
          <label className="task-form__check">
            <input
              type="checkbox"
              checked={values.multiple}
              onChange={(e) =>
                setValues((prev) => ({
                  ...prev,
                  multiple: e.target.checked,
                  correct: e.target.checked ? prev.correct : prev.correct.slice(0, 1),
                }))
              }
            />
            <span>Несколько верных вариантов</span>
          </label>
          {values.options.map((option, index) => (
            // Rows are edited in place and have no id until saved.
            // oxlint-disable-next-line react/no-array-index-key
            <div key={index} className="task-form__option">
              <input
                type={values.multiple ? 'checkbox' : 'radio'}
                name="task-correct"
                aria-label={`Вариант ${index + 1} верный`}
                checked={values.correct.includes(index)}
                onChange={() => markCorrect(index)}
              />
              <TextField
                id={`task-option-${index}`}
                label={`Вариант ${index + 1}`}
                hideLabel
                placeholder={`Вариант ${index + 1}`}
                value={option}
                maxLength={500}
                onChange={(e) => setOption(index, e.target.value)}
              />
              <Button
                variant="ghost"
                size="inline"
                disabled={values.options.length <= 2}
                aria-label={`Удалить вариант ${index + 1}`}
                onClick={() => removeOption(index)}
              >
                Удалить
              </Button>
            </div>
          ))}
          <Button
            variant="ghost"
            size="inline"
            disabled={values.options.length >= 8}
            onClick={() => set('options', [...values.options, ''])}
          >
            Добавить вариант
          </Button>
        </fieldset>
      ) : (
        <>
          <fieldset className="task-form__group">
            <legend>
              Группы тестов: один запуск программы на группу, вывод до {MAX_EXPECTED_OUTPUT}{' '}
              символов
            </legend>
            {values.groups.map((group, index) => (
              // Rows are edited in place and have no id until saved.
              // oxlint-disable-next-line react/no-array-index-key
              <div key={index} className="task-form__test">
                <TextArea
                  id={`task-input-${index}`}
                  label={`Группа ${index + 1}: ввод`}
                  value={group.input}
                  onChange={(e) => setGroup(index, { input: e.target.value })}
                />
                <TextArea
                  id={`task-expected-${index}`}
                  label="Ожидаемый вывод"
                  value={group.expected}
                  onChange={(e) => setGroup(index, { expected: e.target.value })}
                />
                <div className="task-form__test-actions">
                  <label className="task-form__check">
                    <input
                      type="checkbox"
                      checked={group.hidden}
                      onChange={(e) => setGroup(index, { hidden: e.target.checked })}
                    />
                    <span>Закрытая: кандидат не видит, решает итог</span>
                  </label>
                  <Button
                    variant="ghost"
                    size="inline"
                    disabled={values.groups.length <= 2}
                    onClick={() =>
                      set(
                        'groups',
                        values.groups.filter((_, position) => position !== index),
                      )
                    }
                  >
                    Удалить группу
                  </Button>
                </div>
              </div>
            ))}
            <Button
              variant="ghost"
              size="inline"
              disabled={values.groups.length >= 8}
              onClick={() =>
                set('groups', [...values.groups, { input: '', expected: '', hidden: true }])
              }
            >
              Добавить группу
            </Button>
          </fieldset>

          <div className="task-form__row">
            <TextField
              id="task-time-limit"
              label="Ограничение времени, с"
              inputMode="decimal"
              value={values.timeLimit}
              onChange={(e) => set('timeLimit', e.target.value)}
            />
            <SelectField
              id="task-reference-language"
              label="Язык эталонного решения"
              value={values.referenceLanguage}
              onChange={(e) => set('referenceLanguage', e.target.value)}
            >
              {LANGUAGES.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.label}
                </option>
              ))}
            </SelectField>
          </div>

          <fieldset className="task-form__group">
            <legend>Языки для кандидата (ничего не выбрано — все)</legend>
            <div className="task-form__chips">
              {LANGUAGES.map((item) => (
                <Chip
                  key={item.id}
                  active={values.languages.includes(item.id)}
                  onClick={() => set('languages', toggle(values.languages, item.id))}
                >
                  {item.label}
                </Chip>
              ))}
            </div>
          </fieldset>

          <div className="task-form__group">
            <p className="task-form__legend">
              Эталонное решение — им проверяются тесты перед публикацией
            </p>
            <CodeEditor
              value={values.referenceCode}
              language={values.referenceLanguage}
              label="Эталонное решение"
              height="260px"
              onChange={(code) => set('referenceCode', code)}
            />
          </div>
        </>
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
