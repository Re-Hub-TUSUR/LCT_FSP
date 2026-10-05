import { useCallback, useEffect, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  TASK_KIND_LABELS,
  assessmentApi,
  assessmentKeys,
  assessmentQueries,
  topicLabel,
} from '@/entities/assessment'
import type {
  AssessmentAttemptDto,
  AttemptDetailDto,
  AttemptTaskDto,
  CodeAnswerDto,
} from '@/entities/assessment'
import { QuizQuestion } from '@/features/answer-quiz'
import { CodeTask } from '@/features/solve-code-task'
import { ApiError, getErrorMessage } from '@/shared/api'
import { Button, QueryState } from '@/shared/ui'
import './assessment-runner.css'

const DRAFT_SAVE_DELAY_MS = 1000

type Props = {
  attemptId: string
  runnerAvailable: boolean
  onFinished: (attempt: AssessmentAttemptDto) => void
}

/** Loads the attempt, then hands it to the runner: local answers start from the saved ones. */
export function AssessmentRunner({ attemptId, runnerAvailable, onFinished }: Props) {
  const queryClient = useQueryClient()
  const attempt = useQuery(assessmentQueries.attempt(attemptId))

  // The cached attempt goes stale the moment answers change, so it must not outlive this screen:
  // returning to the test loads the saved answers instead of the ones from the first load.
  useEffect(
    () => () => queryClient.removeQueries({ queryKey: assessmentKeys.attempt(attemptId) }),
    [queryClient, attemptId],
  )

  return (
    <QueryState query={attempt} loadingLabel="Загружаем тест…">
      {(data) => (
        <Runner
          key={data.id}
          attempt={data}
          runnerAvailable={runnerAvailable}
          onFinished={onFinished}
        />
      )}
    </QueryState>
  )
}

function formatClock(ms: number) {
  const total = Math.max(0, Math.ceil(ms / 1000))
  return `${String(Math.floor(total / 60)).padStart(2, '0')}:${String(total % 60).padStart(2, '0')}`
}

type RunnerProps = Omit<Props, 'attemptId'> & { attempt: AttemptDetailDto }

function Runner({ attempt, runnerAvailable, onFinished }: RunnerProps) {
  const queryClient = useQueryClient()
  const { tasks } = attempt
  const [index, setIndex] = useState(0)
  const [selected, setSelected] = useState<Record<string, number[]>>(() =>
    Object.fromEntries(tasks.map((task) => [task.id, task.selected ?? []])),
  )
  const [drafts, setDrafts] = useState<Record<string, CodeAnswerDto>>(() =>
    Object.fromEntries(tasks.flatMap((task) => (task.draft ? [[task.id, task.draft]] : []))),
  )
  const [runsLeft, setRunsLeft] = useState(attempt.runsLeft)
  const [confirming, setConfirming] = useState(false)
  const [saveError, setSaveError] = useState('')

  // The countdown follows the server clock, not the device one.
  const { clockOffset } = attempt
  const [now, setNow] = useState(() => Date.now())
  const remaining = Date.parse(attempt.expiresAt) - (now + clockOffset)
  const timeIsUp = remaining <= 0

  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(timer)
  }, [])

  // Code drafts that changed since the last save, flushed after a pause and before finishing.
  const dirty = useRef(new Map<string, CodeAnswerDto>())

  const flushDrafts = useCallback(async () => {
    const pending = [...dirty.current.entries()]
    dirty.current.clear()
    await Promise.all(
      pending.map(([taskId, draft]) =>
        assessmentApi.saveAnswer(attempt.id, { taskId, ...draft }).catch((error: unknown) => {
          // Too late to save is fine: the last saved version will be checked.
          if (!(error instanceof ApiError && error.code === 'attempt_expired')) throw error
        }),
      ),
    )
  }, [attempt.id])

  const saveTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)
  // Leaving the page mid-typing saves the draft at once instead of dropping the pending save.
  useEffect(
    () => () => {
      clearTimeout(saveTimer.current)
      void flushDrafts().catch(() => {})
    },
    [flushDrafts],
  )

  const finish = useMutation({
    mutationFn: async () => {
      await flushDrafts()
      return assessmentApi.finish(attempt.id)
    },
    onSuccess: (result) => {
      void queryClient.invalidateQueries({ queryKey: assessmentKeys.status() })
      queryClient.removeQueries({ queryKey: assessmentKeys.attempt(attempt.id) })
      onFinished(result)
    },
  })

  // When the time runs out the test ends by itself with whatever is saved.
  const { mutate: finishNow, isIdle: finishIdle } = finish
  useEffect(() => {
    if (timeIsUp && finishIdle) finishNow()
  }, [timeIsUp, finishIdle, finishNow])

  // Leaving the tab is only recorded for reviewers; it never changes the score.
  useEffect(() => {
    const onBlur = () => void assessmentApi.signal(attempt.id, 'blur').catch(() => {})
    window.addEventListener('blur', onBlur)
    return () => window.removeEventListener('blur', onBlur)
  }, [attempt.id])

  const selectOptions = (task: AttemptTaskDto, positions: number[]) => {
    setSelected((prev) => ({ ...prev, [task.id]: positions }))
    assessmentApi.saveAnswer(attempt.id, { taskId: task.id, selected: positions }).then(
      () => setSaveError(''),
      (error: unknown) => setSaveError(getErrorMessage(error)),
    )
  }

  const changeDraft = (task: AttemptTaskDto, draft: CodeAnswerDto) => {
    dirty.current.set(task.id, draft)
    setDrafts((prev) => ({ ...prev, [task.id]: draft }))
    clearTimeout(saveTimer.current)
    saveTimer.current = setTimeout(() => {
      flushDrafts().then(
        () => setSaveError(''),
        (error: unknown) => setSaveError(getErrorMessage(error)),
      )
    }, DRAFT_SAVE_DELAY_MS)
  }

  const isAnswered = (task: AttemptTaskDto) =>
    task.kind === 'quiz' ? (selected[task.id]?.length ?? 0) > 0 : task.id in drafts
  const answered = tasks.filter(isAnswered).length
  const task = tasks[index]
  const locked = timeIsUp || finish.isPending

  if (!task) return null

  return (
    <section className="runner" aria-label={`Тест: ${attempt.title}`}>
      <header className="runner__bar">
        <div>
          <p className="runner__eyebrow">{attempt.title}</p>
          <p className="runner__progress">
            Отвечено {answered} из {tasks.length}
          </p>
        </div>
        <p
          className={`runner__clock${remaining < 5 * 60_000 ? ' runner__clock--low' : ''}`}
          role="timer"
          aria-label="Осталось времени"
        >
          {formatClock(remaining)}
        </p>
      </header>

      <nav className="runner__nav" aria-label="Задания">
        {tasks.map((item, position) => (
          <button
            key={item.id}
            type="button"
            className={[
              'runner__step',
              position === index && 'is-current',
              isAnswered(item) && 'is-answered',
            ]
              .filter(Boolean)
              .join(' ')}
            aria-current={position === index ? 'step' : undefined}
            aria-label={`Задание ${position + 1}, ${TASK_KIND_LABELS[item.kind].toLowerCase()}${isAnswered(item) ? ', есть ответ' : ''}`}
            onClick={() => setIndex(position)}
          >
            {item.kind === 'code' ? '</>' : position + 1}
          </button>
        ))}
      </nav>

      <div className="runner__task">
        <p className="runner__eyebrow">
          Задание {index + 1} · {topicLabel(task.topic)}
        </p>
        {task.kind === 'quiz' ? (
          <QuizQuestion
            task={task}
            selected={selected[task.id] ?? []}
            disabled={locked}
            onChange={(positions) => selectOptions(task, positions)}
          />
        ) : (
          <CodeTask
            attemptId={attempt.id}
            task={task}
            draft={drafts[task.id] ?? null}
            runsLeft={runsLeft}
            runnerAvailable={runnerAvailable}
            disabled={locked}
            onDraftChange={(draft) => changeDraft(task, draft)}
            onRunsLeft={setRunsLeft}
          />
        )}
      </div>

      {(saveError || finish.isError) && (
        <p className="runner__error" role="alert">
          {finish.isError
            ? `Не удалось завершить тест: ${getErrorMessage(finish.error)}`
            : `Ответ не сохранился: ${saveError}`}
        </p>
      )}

      <footer className="runner__footer">
        <div className="runner__pager">
          <Button
            variant="ghost"
            size="inline"
            disabled={index === 0}
            onClick={() => setIndex(index - 1)}
          >
            Назад
          </Button>
          <Button
            variant="ghost"
            size="inline"
            disabled={index === tasks.length - 1}
            onClick={() => setIndex(index + 1)}
          >
            Далее
          </Button>
        </div>

        {confirming ? (
          <div className="runner__confirm" role="group" aria-label="Подтверждение завершения">
            <p>
              {answered < tasks.length
                ? `Без ответа: ${tasks.length - answered}. Завершить тест?`
                : 'Завершить тест и отправить на проверку?'}
            </p>
            <Button size="inline" disabled={finish.isPending} onClick={() => finish.mutate()}>
              {finish.isPending ? 'Проверяем…' : 'Да, завершить'}
            </Button>
            <Button
              variant="ghost"
              size="inline"
              disabled={finish.isPending}
              onClick={() => setConfirming(false)}
            >
              Вернуться
            </Button>
          </div>
        ) : (
          <Button size="inline" disabled={finish.isPending} onClick={() => setConfirming(true)}>
            {finish.isPending ? 'Проверяем…' : 'Завершить тест'}
          </Button>
        )}
      </footer>
    </section>
  )
}
