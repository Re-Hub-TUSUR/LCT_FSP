import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  DIFFICULTY_LABELS,
  TASK_KIND_LABELS,
  bankApi,
  bankKeys,
  topicLabel,
} from '@/entities/assessment'
import type {
  BankScope,
  BankTaskDto,
  BankTestDto,
  CompositionRuleDto,
  TaskDifficulty,
  TaskKind,
} from '@/entities/assessment'
import { GRADES, GRADE_LABELS } from '@/entities/category'
import { getErrorMessage } from '@/shared/api'
import { Button, Chip, SelectField, TextField } from '@/shared/ui'

type Props = {
  scope: BankScope
  test?: BankTestDto
  /** Tasks the author may put into a fixed test. */
  tasks: BankTaskDto[]
  onDone: () => void
}

const NEW_RULE: CompositionRuleDto = {
  kind: 'quiz',
  count: 5,
  difficulty: [],
  topics: [],
  scope: 'any',
}

const SCOPE_LABELS: Record<CompositionRuleDto['scope'], string> = {
  specialization: 'По специализации кандидата',
  general: 'Общие',
  any: 'Любые подходящие',
}

const toggle = <T,>(list: T[], item: T) =>
  list.includes(item) ? list.filter((value) => value !== item) : [...list, item]

/**
 * Test template. Admins draw variants by rules; an employer's test is a fixed list of tasks.
 * Reuses the `task-form` layout classes that arrive with `TaskForm` on the same screen.
 */
export function TestForm({ scope, test, tasks, onDone }: Props) {
  const queryClient = useQueryClient()
  const composition = test?.composition
  const [title, setTitle] = useState(test?.title ?? '')
  const [grade, setGrade] = useState(test?.grade ?? '')
  const [duration, setDuration] = useState(String(test?.durationMinutes ?? 30))
  const [passScore, setPassScore] = useState(String(test?.passScore ?? 60))
  const [quizWeight, setQuizWeight] = useState(String(test?.quizWeight ?? 40))
  const [isActive, setIsActive] = useState(test?.isActive ?? true)
  const [mode, setMode] = useState<'rules' | 'fixed'>(
    scope === 'employer' ? 'fixed' : (composition?.mode ?? 'rules'),
  )
  const [rules, setRules] = useState<CompositionRuleDto[]>(
    composition?.mode === 'rules' ? composition.rules : [NEW_RULE],
  )
  const [taskIds, setTaskIds] = useState<string[]>(
    composition?.mode === 'fixed' ? composition.taskIds : [],
  )
  const [problem, setProblem] = useState<string | null>(null)

  const save = useMutation({
    mutationFn: () =>
      bankApi.saveTest(
        scope,
        {
          title: title.trim(),
          grade: scope === 'admin' && grade ? grade : null,
          durationMinutes: Number(duration),
          passScore: Number(passScore),
          quizWeight: Number(quizWeight),
          composition: mode === 'rules' ? { mode, rules } : { mode, taskIds },
          isActive,
        },
        test?.id,
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: bankKeys.tests(scope) })
      onDone()
    },
  })

  const validate = () => {
    if (!title.trim()) return 'Укажите название теста'
    const minutes = Number(duration)
    if (!(minutes >= 5 && minutes <= 180)) return 'Длительность — от 5 до 180 минут'
    if (![passScore, quizWeight].every((value) => Number(value) >= 0 && Number(value) <= 100))
      return 'Проходной балл и вес вопросов — от 0 до 100'
    if (mode === 'fixed' && taskIds.length === 0) return 'Выберите хотя бы одну задачу'
    if (mode === 'rules' && rules.some((rule) => !(rule.count >= 1 && rule.count <= 40)))
      return 'В каждом правиле — от 1 до 40 заданий'
    return null
  }

  const onSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const found = validate()
    setProblem(found)
    if (!found) save.mutate()
  }

  const setRule = (index: number, patch: Partial<CompositionRuleDto>) =>
    setRules((prev) =>
      prev.map((rule, position) => (position === index ? { ...rule, ...patch } : rule)),
    )

  return (
    <form className="task-form" noValidate onSubmit={onSubmit}>
      <h3 className="task-form__heading">{test ? 'Редактирование теста' : 'Новый тест'}</h3>

      <TextField
        id="test-title"
        label="Название"
        value={title}
        maxLength={200}
        onChange={(e) => setTitle(e.target.value)}
      />

      <div className="task-form__row">
        {scope === 'admin' && (
          <SelectField
            id="test-grade"
            label="Подтверждает грейд"
            value={grade}
            onChange={(e) => setGrade(e.target.value)}
          >
            <option value="">Не привязан</option>
            {GRADES.map((code) => (
              <option key={code} value={code}>
                {GRADE_LABELS[code]}
              </option>
            ))}
          </SelectField>
        )}
        <TextField
          id="test-duration"
          label="Длительность, мин"
          inputMode="numeric"
          value={duration}
          onChange={(e) => setDuration(e.target.value)}
        />
        <TextField
          id="test-pass-score"
          label="Проходной балл, из 100"
          inputMode="numeric"
          value={passScore}
          onChange={(e) => setPassScore(e.target.value)}
        />
        <TextField
          id="test-quiz-weight"
          label="Вес вопросов, % (остальное — код)"
          inputMode="numeric"
          value={quizWeight}
          onChange={(e) => setQuizWeight(e.target.value)}
        />
      </div>

      {scope === 'admin' && (
        <SelectField
          id="test-mode"
          label="Состав"
          value={mode}
          onChange={(e) => setMode(e.target.value as 'rules' | 'fixed')}
        >
          <option value="rules">По правилам: случайный вариант из банка</option>
          <option value="fixed">Фиксированный список задач</option>
        </SelectField>
      )}

      {mode === 'rules' ? (
        <fieldset className="task-form__group">
          <legend>Правила выборки</legend>
          {rules.map((rule, index) => (
            // Rules are edited in place and have no id of their own.
            // oxlint-disable-next-line react/no-array-index-key
            <div key={index} className="task-form__test">
              <SelectField
                id={`rule-kind-${index}`}
                label="Тип"
                value={rule.kind}
                onChange={(e) => setRule(index, { kind: e.target.value as TaskKind })}
              >
                {Object.entries(TASK_KIND_LABELS).map(([code, label]) => (
                  <option key={code} value={code}>
                    {label}
                  </option>
                ))}
              </SelectField>
              <TextField
                id={`rule-count-${index}`}
                label="Сколько"
                inputMode="numeric"
                value={String(rule.count)}
                onChange={(e) => setRule(index, { count: Number(e.target.value) || 0 })}
              />
              <SelectField
                id={`rule-scope-${index}`}
                label="Откуда"
                value={rule.scope}
                onChange={(e) =>
                  setRule(index, { scope: e.target.value as CompositionRuleDto['scope'] })
                }
              >
                {Object.entries(SCOPE_LABELS).map(([code, label]) => (
                  <option key={code} value={code}>
                    {label}
                  </option>
                ))}
              </SelectField>
              <TextField
                id={`rule-topics-${index}`}
                label="Темы через запятую (пусто — любые)"
                value={rule.topics.join(', ')}
                onChange={(e) =>
                  setRule(index, {
                    topics: e.target.value
                      .split(',')
                      .map((topic) => topic.trim())
                      .filter(Boolean),
                  })
                }
              />
              <div className="task-form__test-actions">
                <div className="task-form__chips" role="group" aria-label="Сложность">
                  {(Object.keys(DIFFICULTY_LABELS) as TaskDifficulty[]).map((code) => (
                    <Chip
                      key={code}
                      active={rule.difficulty.includes(code)}
                      onClick={() => setRule(index, { difficulty: toggle(rule.difficulty, code) })}
                    >
                      {DIFFICULTY_LABELS[code]}
                    </Chip>
                  ))}
                </div>
                <Button
                  variant="ghost"
                  size="inline"
                  disabled={rules.length <= 1}
                  onClick={() => setRules(rules.filter((_, position) => position !== index))}
                >
                  Удалить правило
                </Button>
              </div>
            </div>
          ))}
          <Button
            variant="ghost"
            size="inline"
            disabled={rules.length >= 12}
            onClick={() => setRules([...rules, NEW_RULE])}
          >
            Добавить правило
          </Button>
        </fieldset>
      ) : (
        <fieldset className="task-form__group">
          <legend>Задачи теста</legend>
          {tasks.length === 0 && (
            <p className="task-form__legend">Сначала добавьте задачи в банк.</p>
          )}
          {tasks.map((task) => (
            <label key={task.id} className="task-form__check">
              <input
                type="checkbox"
                checked={taskIds.includes(task.id)}
                onChange={() => setTaskIds(toggle(taskIds, task.id))}
              />
              <span>
                {TASK_KIND_LABELS[task.kind]} · {topicLabel(task.topic)} · {task.title}
              </span>
            </label>
          ))}
        </fieldset>
      )}

      <label className="task-form__check">
        <input type="checkbox" checked={isActive} onChange={(e) => setIsActive(e.target.checked)} />
        <span>Активен</span>
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
