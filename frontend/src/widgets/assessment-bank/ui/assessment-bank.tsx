import { useRef, useState } from 'react'
import type { ChangeEvent, FormEvent } from 'react'
import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
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
import { downloadJson } from '@/shared/lib'
import { Button, Chip, ConfirmDialog, Pagination, QueryState, Section } from '@/shared/ui'
import { TestForm } from './test-form'
import './assessment-bank.css'

type TaskEditor = { kind: TaskKind; task?: BankTaskDto }
type TestEditor = { test?: BankTestDto }
type Removal = { type: 'task' | 'test'; id: string; title: string }

/** What an author may add. Hand-graded questions exist only in a company's own tests. */
const NEW_TASK_LABELS: Record<TaskKind, string> = {
  quiz: 'Добавить вопрос',
  code: 'Добавить задачу на код',
  open: 'Добавить открытый вопрос',
}
const KINDS_BY_SCOPE: Record<BankScope, TaskKind[]> = {
  admin: ['quiz', 'code'],
  employer: ['quiz', 'code', 'open'],
}

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
  const [page, setPage] = useState(1)
  const [perPage, setPerPage] = useState(10)
  const [kind, setKind] = useState<TaskKind | undefined>()
  const [search, setSearch] = useState('')
  const [text, setText] = useState('')
  const tasks = useQuery({
    ...bankQueries.tasks(scope, { page, perPage, kind, q: search || undefined }),
    placeholderData: keepPreviousData,
  })
  const tests = useQuery(bankQueries.tests(scope))
  const [taskEditor, setTaskEditor] = useState<TaskEditor | null>(null)
  const [testEditor, setTestEditor] = useState<TestEditor | null>(null)
  // A fixed test is composed from the whole bank, not from the page on screen.
  const everyTask = useQuery({
    ...bankQueries.tasks(scope, { perPage: 100 }),
    enabled: testEditor !== null,
  })
  const [checks, setChecks] = useState<Record<string, TaskCheckDto>>({})
  const [removal, setRemoval] = useState<Removal | null>(null)
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')
  const fileInput = useRef<HTMLInputElement>(null)

  const onError = (cause: unknown) => {
    setNotice('')
    setError(getErrorMessage(cause))
  }

  const remove = useMutation({
    mutationFn: ({ type, id }: Removal) =>
      type === 'task' ? bankApi.deleteTask(scope, id) : bankApi.deleteTest(scope, id),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: bankKeys.all(scope) }),
    onError,
    onSettled: () => setRemoval(null),
  })
  const check = useMutation({
    mutationFn: (id: string) => bankApi.checkTask(scope, id),
    onSuccess: (result, id) => setChecks((prev) => ({ ...prev, [id]: result })),
    onError,
  })
  const exportTasks = useMutation({
    mutationFn: () => bankApi.exportTasks(scope),
    onSuccess: (items) => {
      downloadJson('assessment-tasks.json', items)
      setError('')
      setNotice(`Выгружено задач: ${items.length}`)
    },
    onError,
  })
  const importTasks = useMutation({
    mutationFn: async (file: File) => {
      const parsed: unknown = JSON.parse(await file.text())
      if (!Array.isArray(parsed)) throw new Error('В файле должен быть список задач')
      return bankApi.importTasks(scope, parsed)
    },
    onSuccess: ({ created }) => {
      void queryClient.invalidateQueries({ queryKey: bankKeys.tasks(scope) })
      setError('')
      setNotice(`Добавлено задач: ${created}`)
    },
    onError: (cause) =>
      onError(cause instanceof SyntaxError ? new Error('Файл не похож на JSON') : cause),
  })

  const onFile = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    // The same file can be picked again after fixing it.
    e.target.value = ''
    if (file) importTasks.mutate(file)
  }

  const onSearch = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setSearch(text.trim())
    setPage(1)
  }

  const pickKind = (next: TaskKind | undefined) => {
    setKind(next)
    setPage(1)
  }

  return (
    <>
      {error && (
        <p className="bank__error" role="alert">
          {error}
        </p>
      )}
      {notice && (
        <p className="bank__note" role="status">
          {notice}
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
              {KINDS_BY_SCOPE[scope].map((item, index) => (
                <Button
                  key={item}
                  variant={index === 0 ? 'solid' : 'ghost'}
                  size="inline"
                  onClick={() => setTaskEditor({ kind: item })}
                >
                  {NEW_TASK_LABELS[item]}
                </Button>
              ))}
              <Button
                variant="ghost"
                size="inline"
                disabled={importTasks.isPending}
                onClick={() => fileInput.current?.click()}
              >
                {importTasks.isPending ? 'Загружаем…' : 'Импорт JSON'}
              </Button>
              <Button
                variant="ghost"
                size="inline"
                disabled={exportTasks.isPending}
                onClick={() => exportTasks.mutate()}
              >
                Экспорт JSON
              </Button>
              <input
                ref={fileInput}
                type="file"
                accept="application/json,.json"
                className="visually-hidden"
                aria-label="Файл с задачами в формате JSON"
                tabIndex={-1}
                onChange={onFile}
              />
            </div>

            <div className="bank__filters">
              <form className="bank__search" role="search" onSubmit={onSearch}>
                <input
                  aria-label="Поиск по названию или теме"
                  placeholder="Название или тема"
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                />
                <button type="submit">Найти</button>
              </form>
              <div className="bank__chips" role="group" aria-label="Тип задания">
                <Chip active={kind === undefined} onClick={() => pickKind(undefined)}>
                  Все
                </Chip>
                {KINDS_BY_SCOPE[scope].map((item) => (
                  <Chip key={item} active={kind === item} onClick={() => pickKind(item)}>
                    {TASK_KIND_LABELS[item]}
                  </Chip>
                ))}
              </div>
            </div>

            <QueryState
              query={tasks}
              isEmpty={(data) => data.items.length === 0}
              emptyTitle={search || kind ? 'Ничего не нашли' : 'В банке пока нет задач'}
            >
              {(data) => (
                <>
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
                        {data.items.map((task) => {
                          const result = checks[task.id]
                          return (
                            <tr key={task.id}>
                              <td>
                                {task.title}
                                {task.warnings?.map((warning) => (
                                  <p key={warning} className="bank__check bank__check--fail">
                                    {warning}
                                  </p>
                                ))}
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
                                {task.kind === 'code' && task.payload.reference && (
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
                                  onClick={() =>
                                    setRemoval({ type: 'task', id: task.id, title: task.title })
                                  }
                                >
                                  Удалить
                                </Button>
                              </td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                  <Pagination
                    page={data.page}
                    pages={data.pages}
                    perPage={data.perPage}
                    total={data.total}
                    onPage={setPage}
                    onPerPage={(size) => {
                      setPerPage(size)
                      setPage(1)
                    }}
                  />
                </>
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
            tasks={everyTask.data?.items ?? []}
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
                            <td>
                              {test.grade ? GRADE_LABELS[test.grade as Grade] : '—'}
                              {test.specialization && ` · ${topicLabel(test.specialization)}`}
                            </td>
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
                              onClick={() =>
                                setRemoval({ type: 'test', id: test.id, title: test.title })
                              }
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

      {removal && (
        <ConfirmDialog
          title={removal.type === 'task' ? 'Удалить задачу?' : 'Удалить тест?'}
          confirmLabel={remove.isPending ? 'Удаляем…' : 'Удалить'}
          busy={remove.isPending}
          onConfirm={() => remove.mutate(removal)}
          onCancel={() => setRemoval(null)}
        >
          «{removal.title}» исчезнет из банка. Уже пройденные попытки сохранят свой результат.
        </ConfirmDialog>
      )}
    </>
  )
}
