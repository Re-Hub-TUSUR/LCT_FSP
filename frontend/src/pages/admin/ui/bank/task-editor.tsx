import { useId, useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Button, Chip, SelectField, TextArea, TextField } from '@/shared/ui'
import { adminApi, adminKeys, adminQueries } from '../../api/admin-api'
import type { AdminTaskDetail, PreviewVariant, TaskKind } from '../../api/types'
import { errorText } from '../../lib/format'
import { DIFFICULTY_LABELS, KIND_LABELS } from '../../lib/labels'
import { emptyForm, toForm, toPayload, undeclared, validate } from '../../model/task-form'
import type { TaskForm } from '../../model/task-form'

type Props = {
  task?: AdminTaskDetail
  /** The id of the saved task, or null when the editor was cancelled. */
  onDone: (taskId: string | null) => void
}

const toggle = (list: string[], item: string) =>
  list.includes(item) ? list.filter((value) => value !== item) : [...list, item]

export function TaskEditor({ task, onDone }: Props) {
  const queryClient = useQueryClient()
  const skillsId = useId()
  const dictionaries = useQuery(adminQueries.dictionaries())
  const skills = useQuery(adminQueries.skills())
  const [form, setForm] = useState<TaskForm>(() => (task ? toForm(task) : emptyForm()))
  const [problem, setProblem] = useState<string | null>(null)
  const [preview, setPreview] = useState<PreviewVariant[] | null>(null)

  const save = useMutation({
    mutationFn: () => {
      const payload = toPayload(form)
      return task
        ? adminApi.updateTask(task.id, payload)
        : adminApi.createTask({ ...payload, status: form.status })
    },
    onSuccess: (saved) => {
      void queryClient.invalidateQueries({ queryKey: adminKeys.bank() })
      onDone(saved.id)
    },
  })
  const draw = useMutation({
    mutationFn: () =>
      adminApi.preview(
        form.statement,
        toPayload(form).variables,
        form.kind === 'quiz' ? form.options.map((option) => option.text).filter(Boolean) : [],
      ),
    onSuccess: setPreview,
  })

  const set = <K extends keyof TaskForm>(key: K, value: TaskForm[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }))
    setProblem(null)
  }

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const found = validate(form)
    setProblem(found)
    if (!found) save.mutate()
  }

  const runPreview = () => {
    const found = form.statement.trim() ? (undeclared(form)[0] ?? null) : null
    if (!form.statement.trim()) return setProblem('Сначала напишите условие')
    if (found) return setProblem(`Объявите переменную «${found}»`)
    draw.mutate()
  }

  // Only specializations the platform knows: the bank rejects the others.
  const specializations = (dictionaries.data?.specializations ?? []).filter(
    (item) => item.inPlatform && !item.isArchived,
  )

  return (
    <form className="admin-form task-editor" noValidate onSubmit={submit}>
      {!task && (
        <div className="admin-chips" role="group" aria-label="Тип задания">
          {(Object.keys(KIND_LABELS) as TaskKind[]).map((kind) => (
            <Chip
              key={kind}
              active={form.kind === kind}
              onClick={() => setForm((prev) => ({ ...emptyForm(kind), ...pickCommon(prev) }))}
            >
              {KIND_LABELS[kind]}
            </Chip>
          ))}
        </div>
      )}

      <TextField
        id="task-title"
        label="Название"
        value={form.title}
        maxLength={200}
        onChange={(event) => set('title', event.target.value)}
      />
      <TextArea
        id="task-statement"
        label="Условие (переменные — в фигурных скобках: {n})"
        value={form.statement}
        rows={6}
        onChange={(event) => set('statement', event.target.value)}
      />

      <div className="admin-form__row">
        <SelectField
          id="task-grade"
          label="Грейд"
          value={form.grade}
          onChange={(event) => set('grade', event.target.value)}
        >
          <option value="">Не указан</option>
          {(dictionaries.data?.grades ?? []).map((grade) => (
            <option key={grade.code} value={grade.code}>
              {grade.label}
            </option>
          ))}
        </SelectField>
        <TextField
          id="task-skill"
          label="Навык"
          value={form.skill}
          maxLength={64}
          list={skillsId}
          onChange={(event) => set('skill', event.target.value)}
        />
        <datalist id={skillsId}>
          {[
            ...new Set([
              ...(skills.data ?? []),
              ...(dictionaries.data?.skills ?? []).map((skill) => skill.name),
            ]),
          ].map((skill) => (
            <option key={skill} value={skill}>
              {skill}
            </option>
          ))}
        </datalist>
        <SelectField
          id="task-difficulty"
          label="Сложность"
          value={form.difficulty}
          onChange={(event) => set('difficulty', event.target.value as TaskForm['difficulty'])}
        >
          {Object.entries(DIFFICULTY_LABELS).map(([code, label]) => (
            <option key={code} value={code}>
              {label}
            </option>
          ))}
        </SelectField>
        <TextField
          id="task-time"
          label="Лимит времени, мин"
          inputMode="numeric"
          value={form.timeLimitMinutes}
          onChange={(event) => set('timeLimitMinutes', event.target.value)}
        />
      </div>

      <fieldset className="admin-fieldset">
        <legend>Специализации (ничего не выбрано — подходит всем)</legend>
        <div className="admin-chips">
          {specializations.map((item) => (
            <Chip
              key={item.code}
              active={form.specializations.includes(item.code)}
              onClick={() => set('specializations', toggle(form.specializations, item.code))}
            >
              {item.label}
            </Chip>
          ))}
        </div>
      </fieldset>

      <fieldset className="admin-fieldset">
        <legend>Переменные и диапазоны</legend>
        {form.variables.map((variable, index) => (
          <div key={index} className="admin-form__row admin-form__row--tight">
            {(['name', 'min', 'max', 'step'] as const).map((field) => (
              <TextField
                key={field}
                id={`variable-${index}-${field}`}
                label={{ name: 'Имя', min: 'От', max: 'До', step: 'Шаг' }[field]}
                value={variable[field]}
                inputMode={field === 'name' ? 'text' : 'decimal'}
                onChange={(event) =>
                  set(
                    'variables',
                    form.variables.map((item, i) =>
                      i === index ? { ...item, [field]: event.target.value } : item,
                    ),
                  )
                }
              />
            ))}
            <Button
              variant="ghost"
              size="inline"
              aria-label={`Удалить переменную ${variable.name}`}
              onClick={() =>
                set(
                  'variables',
                  form.variables.filter((_, i) => i !== index),
                )
              }
            >
              ×
            </Button>
          </div>
        ))}
        <div className="admin-form__actions">
          <Button
            variant="ghost"
            size="inline"
            disabled={form.variables.length >= 10}
            onClick={() =>
              set('variables', [...form.variables, { name: '', min: '1', max: '10', step: '1' }])
            }
          >
            Добавить переменную
          </Button>
          <Button variant="ghost" size="inline" disabled={draw.isPending} onClick={runPreview}>
            {draw.isPending ? 'Подставляем…' : 'Предпросмотр 3 вариантов'}
          </Button>
        </div>
        {draw.isError && <p className="admin-error">{errorText(draw.error)}</p>}
        {preview && (
          <div className="preview" aria-label="Варианты задания">
            {preview.map((variant, index) => (
              <article key={index} className="preview__card">
                <p className="preview__values">
                  Вариант {index + 1}:{' '}
                  {Object.entries(variant.values)
                    .map(([name, value]) => `${name} = ${value}`)
                    .join(', ') || 'без переменных'}
                </p>
                <p className="preview__statement">{variant.statement}</p>
                {variant.options.length > 0 && (
                  <ul className="preview__options">
                    {variant.options.map((option, i) => (
                      <li key={i}>{option}</li>
                    ))}
                  </ul>
                )}
              </article>
            ))}
          </div>
        )}
      </fieldset>

      {form.kind === 'quiz' ? (
        <QuizFields form={form} set={set} />
      ) : (
        <CodeFields form={form} set={set} />
      )}

      {!task && (
        <div className="admin-chips" role="group" aria-label="Статус после сохранения">
          <Chip active={form.status === 'draft'} onClick={() => set('status', 'draft')}>
            Сохранить черновиком
          </Chip>
          <Chip active={form.status === 'active'} onClick={() => set('status', 'active')}>
            Сразу активным
          </Chip>
        </div>
      )}

      {(problem || save.isError) && (
        <p className="admin-error" role="alert">
          {problem ?? errorText(save.error)}
        </p>
      )}
      <div className="admin-form__actions">
        <Button type="submit" size="inline" disabled={save.isPending}>
          {save.isPending ? 'Сохраняем…' : 'Сохранить'}
        </Button>
        <Button
          variant="ghost"
          size="inline"
          disabled={save.isPending}
          onClick={() => onDone(null)}
        >
          Отмена
        </Button>
      </div>
    </form>
  )
}

/** What survives switching the kind of a new task. */
function pickCommon(form: TaskForm): Partial<TaskForm> {
  const {
    title,
    statement,
    specializations,
    grade,
    skill,
    difficulty,
    timeLimitMinutes,
    variables,
  } = form
  return {
    title,
    statement,
    specializations,
    grade,
    skill,
    difficulty,
    timeLimitMinutes,
    variables,
  }
}

type FieldsProps = {
  form: TaskForm
  set: <K extends keyof TaskForm>(key: K, value: TaskForm[K]) => void
}

function QuizFields({ form, set }: FieldsProps) {
  return (
    <fieldset className="admin-fieldset">
      <legend>Варианты ответа (отметьте правильные)</legend>
      <label className="admin-check">
        <input
          type="checkbox"
          checked={form.multiple}
          onChange={(event) => set('multiple', event.target.checked)}
        />
        <span>Несколько правильных ответов</span>
      </label>
      {form.options.map((option, index) => (
        <div key={index} className="admin-form__row admin-form__row--tight">
          <label className="admin-check">
            <input
              type={form.multiple ? 'checkbox' : 'radio'}
              name="quiz-correct"
              checked={option.correct}
              onChange={(event) =>
                set(
                  'options',
                  form.options.map((item, i) => ({
                    ...item,
                    correct: i === index ? event.target.checked : form.multiple && item.correct,
                  })),
                )
              }
            />
            <span className="visually-hidden">Правильный</span>
          </label>
          <TextField
            id={`option-${index}`}
            label={`Вариант ${index + 1}`}
            value={option.text}
            maxLength={500}
            onChange={(event) =>
              set(
                'options',
                form.options.map((item, i) =>
                  i === index ? { ...item, text: event.target.value } : item,
                ),
              )
            }
          />
          <Button
            variant="ghost"
            size="inline"
            aria-label={`Удалить вариант ${index + 1}`}
            disabled={form.options.length <= 2}
            onClick={() =>
              set(
                'options',
                form.options.filter((_, i) => i !== index),
              )
            }
          >
            ×
          </Button>
        </div>
      ))}
      <Button
        variant="ghost"
        size="inline"
        disabled={form.options.length >= 8}
        onClick={() => set('options', [...form.options, { text: '', correct: false }])}
      >
        Добавить вариант
      </Button>
    </fieldset>
  )
}

function CodeFields({ form, set }: FieldsProps) {
  return (
    <fieldset className="admin-fieldset">
      <legend>Код: языки и тест-кейсы</legend>
      <div className="admin-form__row">
        <TextField
          id="code-languages"
          label="Языки (id через запятую, пусто — любые)"
          value={form.languages}
          placeholder="python-3.14, go-1.23"
          onChange={(event) => set('languages', event.target.value)}
        />
        <TextField
          id="code-run-limit"
          label="Лимит запуска, с"
          inputMode="decimal"
          value={form.runLimitSeconds}
          onChange={(event) => set('runLimitSeconds', event.target.value)}
        />
      </div>
      {form.groups.map((group, index) => (
        <div key={index} className="admin-form__row admin-form__row--tight">
          <TextArea
            id={`group-${index}-input`}
            label={`Ввод ${index + 1}`}
            rows={2}
            value={group.input}
            onChange={(event) =>
              set(
                'groups',
                form.groups.map((item, i) =>
                  i === index ? { ...item, input: event.target.value } : item,
                ),
              )
            }
          />
          <TextArea
            id={`group-${index}-expected`}
            label="Ожидаемый вывод"
            rows={2}
            value={group.expected}
            onChange={(event) =>
              set(
                'groups',
                form.groups.map((item, i) =>
                  i === index ? { ...item, expected: event.target.value } : item,
                ),
              )
            }
          />
          <label className="admin-check">
            <input
              type="checkbox"
              checked={group.hidden}
              onChange={(event) =>
                set(
                  'groups',
                  form.groups.map((item, i) =>
                    i === index ? { ...item, hidden: event.target.checked } : item,
                  ),
                )
              }
            />
            <span>Скрытый</span>
          </label>
          {group.hidden && (
            <TextField
              id={`group-${index}-weight`}
              label="Вес"
              type="number"
              min={1}
              max={10}
              value={String(group.weight ?? 1)}
              onChange={(event) =>
                set(
                  'groups',
                  form.groups.map((item, i) =>
                    i === index ? { ...item, weight: Number(event.target.value) } : item,
                  ),
                )
              }
            />
          )}
          <Button
            variant="ghost"
            size="inline"
            aria-label={`Удалить тест-кейс ${index + 1}`}
            disabled={form.groups.length <= 2}
            onClick={() =>
              set(
                'groups',
                form.groups.filter((_, i) => i !== index),
              )
            }
          >
            ×
          </Button>
        </div>
      ))}
      <Button
        variant="ghost"
        size="inline"
        disabled={form.groups.length >= 8}
        onClick={() => set('groups', [...form.groups, { input: '', expected: '', hidden: true }])}
      >
        Добавить тест-кейс
      </Button>
      <div className="admin-form__row">
        <TextField
          id="code-reference-language"
          label="Эталон: язык (необязательно)"
          value={form.referenceLanguage}
          onChange={(event) => set('referenceLanguage', event.target.value)}
        />
      </div>
      <TextArea
        id="code-reference"
        label="Эталонное решение"
        rows={5}
        value={form.referenceCode}
        onChange={(event) => set('referenceCode', event.target.value)}
      />
      <div className="admin-form__row">
        <TextField
          id="code-starter-language"
          label="Стартовый код: язык (необязательно)"
          value={form.starterLanguage}
          placeholder="python-3.14"
          onChange={(event) => set('starterLanguage', event.target.value)}
        />
      </div>
      <TextArea
        id="code-starter"
        label="Стартовый код — программа с ошибкой, которую кандидат получит в редакторе"
        rows={5}
        value={form.starterCode}
        onChange={(event) => set('starterCode', event.target.value)}
      />
    </fieldset>
  )
}
