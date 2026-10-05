import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  DIFFICULTY_LABELS,
  TASK_KIND_LABELS,
  VERDICT_LABELS,
  bankApi,
  bankKeys,
  bankQueries,
  topicLabel,
} from '@/entities/assessment'
import type {
  BankScope,
  BankTaskDto,
  BankTestDto,
  TaskCheckDto,
  TaskKind,
} from '@/entities/assessment'
import { GRADE_LABELS } from '@/entities/category'
import type { Grade } from '@/entities/category'
import { TaskForm } from '@/features/edit-assessment-task'
import { getErrorMessage } from '@/shared/api'
import { Button, QueryState, Section } from '@/shared/ui'
import { TestForm } from './test-form'
import './assessment-bank.css'

type TaskEditor = { kind: TaskKind; task?: BankTaskDto }
type TestEditor = { test?: BankTestDto }

function describeComposition(test: BankTestDto) {
  const { composition } = test
  if (composition.mode === 'fixed') return `${composition.taskIds.length} зад. по списку`
  return composition.rules
    .map((rule) => `${rule.count} × ${TASK_KIND_LABELS[rule.kind].toLowerCase()}`)
    .join(' + ')
}

/** Task bank and test templates of one author: the platform (admin) or an employer. */
export function AssessmentBank({ scope }: { scope: BankScope }) {
  const queryClient = useQueryClient()
  const tasks = useQuery(bankQueries.tasks(scope))
  const tests = useQuery(bankQueries.tests(scope))
  const [taskEditor, setTaskEditor] = useState<TaskEditor | null>(null)
  const [testEditor, setTestEditor] = useState<TestEditor | null>(null)
  const [checks, setChecks] = useState<Record<string, TaskCheckDto>>({})
  const [error, setError] = useState('')

  const onError = (cause: unknown) => setError(getErrorMessage(cause))

  const removeTask = useMutation({
    mutationFn: (id: string) => bankApi.deleteTask(scope, id),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: bankKeys.all(scope) }),
    onError,
  })
  const removeTest = useMutation({
    mutationFn: (id: string) => bankApi.deleteTest(scope, id),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: bankKeys.tests(scope) }),
    onError,
  })
  const check = useMutation({
    mutationFn: (id: string) => bankApi.checkTask(scope, id),
    onSuccess: (result, id) => setChecks((prev) => ({ ...prev, [id]: result })),
    onError,
  })

  return (
    <>
      {error && (
        <p className="bank__error" role="alert">
          {error}
        </p>
      )}

      <Section title="Банк задач">
        {taskEditor ? (
          <TaskForm
            key={taskEditor.task?.id ?? taskEditor.kind}
            scope={scope}
            kind={taskEditor.kind}
            task={taskEditor.task}
            onDone={() => setTaskEditor(null)}
          />
        ) : (
          <>
            <div className="bank__toolbar">
              <Button size="inline" onClick={() => setTaskEditor({ kind: 'quiz' })}>
                Добавить вопрос
              </Button>
              <Button variant="ghost" size="inline" onClick={() => setTaskEditor({ kind: 'code' })}>
                Добавить задачу на код
              </Button>
            </div>
            <QueryState
              query={tasks}
              isEmpty={(page) => page.items.length === 0}
              emptyTitle="В банке пока нет задач"
            >
              {(page) => (
                <div className="bank__scroll">
                  <table className="bank__table">
                    <thead>
                      <tr>
                        <th scope="col">Задача</th>
                        <th scope="col">Тип</th>
                        <th scope="col">Тема</th>
                        <th scope="col">Сложность</th>
                        <th scope="col">Статус</th>
                        <th scope="col">Действия</th>
                      </tr>
                    </thead>
                    <tbody>
                      {page.items.map((task) => {
                        const result = checks[task.id]
                        return (
                          <tr key={task.id}>
                            <td>
                              {task.title}
                              {result && (
                                <p
                                  className={`bank__check bank__check--${result.ok ? 'ok' : 'fail'}`}
                                  role="status"
                                >
                                  {result.ok
                                    ? 'Эталон прошёл все группы тестов'
                                    : `Эталон не прошёл: ${result.groups
                                        .map(
                                          (group, index) =>
                                            `группа ${index + 1} — ${VERDICT_LABELS[group.verdict].toLowerCase()}`,
                                        )
                                        .join('; ')}`}
                                </p>
                              )}
                            </td>
                            <td>{TASK_KIND_LABELS[task.kind]}</td>
                            <td>{topicLabel(task.topic)}</td>
                            <td>{DIFFICULTY_LABELS[task.difficulty]}</td>
                            <td>{task.isActive ? 'Активна' : 'Выключена'}</td>
                            <td className="bank__actions">
                              <Button
                                variant="ghost"
                                size="inline"
                                onClick={() => setTaskEditor({ kind: task.kind, task })}
                              >
                                Изменить
                              </Button>
                              {task.kind === 'code' && task.code?.reference && (
                                <Button
                                  variant="ghost"
                                  size="inline"
                                  disabled={check.isPending}
                                  onClick={() => check.mutate(task.id)}
                                >
                                  {check.isPending && check.variables === task.id
                                    ? 'Проверяем…'
                                    : 'Проверить эталоном'}
                                </Button>
                              )}
                              <Button
                                variant="ghost"
                                size="inline"
                                disabled={removeTask.isPending}
                                onClick={() => {
                                  if (window.confirm(`Удалить «${task.title}»?`))
                                    removeTask.mutate(task.id)
                                }}
                              >
                                Удалить
                              </Button>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                  {page.total > page.items.length && (
                    <p className="bank__note">
                      Показаны последние {page.items.length} из {page.total}.
                    </p>
                  )}
                </div>
              )}
            </QueryState>
          </>
        )}
      </Section>

      <Section title={scope === 'admin' ? 'Тесты на грейд' : 'Тесты компании'}>
        {testEditor ? (
          <TestForm
            key={testEditor.test?.id ?? 'new'}
            scope={scope}
            test={testEditor.test}
            tasks={tasks.data?.items ?? []}
            onDone={() => setTestEditor(null)}
          />
        ) : (
          <>
            <div className="bank__toolbar">
              <Button size="inline" onClick={() => setTestEditor({})}>
                Добавить тест
              </Button>
            </div>
            <QueryState
              query={tests}
              isEmpty={(items) => items.length === 0}
              emptyTitle="Тестов пока нет"
            >
              {(items) => (
                <div className="bank__scroll">
                  <table className="bank__table">
                    <thead>
                      <tr>
                        <th scope="col">Тест</th>
                        {scope === 'admin' && <th scope="col">Грейд</th>}
                        <th scope="col">Время</th>
                        <th scope="col">Состав</th>
                        <th scope="col">Статус</th>
                        <th scope="col">Действия</th>
                      </tr>
                    </thead>
                    <tbody>
                      {items.map((test) => (
                        <tr key={test.id}>
                          <td>{test.title}</td>
                          {scope === 'admin' && (
                            <td>{test.grade ? GRADE_LABELS[test.grade as Grade] : '—'}</td>
                          )}
                          <td>{test.durationMinutes} мин</td>
                          <td>{describeComposition(test)}</td>
                          <td>{test.isActive ? 'Активен' : 'Выключен'}</td>
                          <td className="bank__actions">
                            <Button
                              variant="ghost"
                              size="inline"
                              onClick={() => setTestEditor({ test })}
                            >
                              Изменить
                            </Button>
                            <Button
                              variant="ghost"
                              size="inline"
                              disabled={removeTest.isPending}
                              onClick={() => {
                                if (window.confirm(`Удалить тест «${test.title}»?`))
                                  removeTest.mutate(test.id)
                              }}
                            >
                              Удалить
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </QueryState>
          </>
        )}
      </Section>
    </>
  )
}
