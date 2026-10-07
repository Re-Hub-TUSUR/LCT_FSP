import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  TASK_KIND_LABELS,
  assessmentApi,
  assessmentKeys,
  assessmentQueries,
  assignmentKeys,
  topicLabel,
} from '@/entities/assessment'
import type {
  AssessmentAttemptDto,
  AttemptDetailDto,
  AttemptTaskDto,
  TaskAnswerDto,
} from '@/entities/assessment'
import { ApiError, getErrorMessage } from '@/shared/api'
import { Button, QueryState } from '@/shared/ui'
import { TASK_TRAITS, TaskView, isAnswered } from '../config/task-views'
import { createDraftSaver } from '../lib/draft-saver'
import { createTaskClock } from '../lib/task-clock'
import './assessment-runner.css'

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
  const [answers, setAnswers] = useState<Record<string, TaskAnswerDto>>(() =>
    Object.fromEntries(tasks.flatMap((task) => (task.answer ? [[task.id, task.answer]] : []))),
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

  // Typed answers (code, text) are saved in the background: after a pause in typing, and
  // every few seconds while the typing goes on without one.
  const [drafts] = useState(() =>
    createDraftSaver<TaskAnswerDto>(
      (taskId, answer) =>
        assessmentApi.saveAnswer(attempt.id, { taskId, answer }).catch((error: unknown) => {
          // Too late to save is fine: the last saved version will be checked.
          if (!(error instanceof ApiError && error.code === 'attempt_expired')) throw error
        }),
      {
        onSaved: () => setSaveError(''),
        onFailed: (error) => setSaveError(getErrorMessage(error)),
      },
    ),
  )
  // Leaving the page mid-typing saves the draft at once instead of dropping the pending save.
  useEffect(() => () => void drafts.flush().catch(() => {}), [drafts])

  // Time on every task, for the analytics of the task bank: reported when the candidate leaves
  // the task. A hidden tab does not count.
  const [clock] = useState(() =>
    createTaskClock((taskId, seconds) => assessmentApi.trackTime(attempt.id, taskId, seconds)),
  )
  const shownId = tasks[index]?.id
  useEffect(() => {
    if (shownId) clock.show(shownId)
  }, [clock, shownId])
  useEffect(() => {
    const onVisibility = () =>
      document.visibilityState === 'hidden' ? clock.pause() : clock.resume()
    document.addEventListener('visibilitychange', onVisibility)
    return () => {
      document.removeEventListener('visibilitychange', onVisibility)
      clock.pause()
    }
  }, [clock])

  const finish = useMutation({
    mutationFn: async () => {
      // Time is accepted only while the attempt runs: it goes before the finish.
      await clock.flush().catch(() => {})
      await drafts.flush()
      return assessmentApi.finish(attempt.id)
    },
    onError: () => clock.resume(),
    onSuccess: (result) => {
      void queryClient.invalidateQueries({ queryKey: assessmentKeys.status() })
      // A test a company sent changes its line in the inbox too.
      void queryClient.invalidateQueries({ queryKey: assignmentKeys.all })
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

  const changeAnswer = (task: AttemptTaskDto, answer: TaskAnswerDto) => {
    setAnswers((prev) => ({ ...prev, [task.id]: answer }))
    if (TASK_TRAITS[task.kind].save === 'draft') return drafts.change(task.id, answer)
    assessmentApi.saveAnswer(attempt.id, { taskId: task.id, answer }).then(
      () => setSaveError(''),
      (error: unknown) => setSaveError(getErrorMessage(error)),
    )
  }

  const answered = tasks.filter((item) => isAnswered(item, answers[item.id])).length
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
              isAnswered(item, answers[item.id]) && 'is-answered',
            ]
              .filter(Boolean)
              .join(' ')}
            aria-current={position === index ? 'step' : undefined}
            aria-label={`Задание ${position + 1}, ${TASK_KIND_LABELS[item.kind].toLowerCase()}${isAnswered(item, answers[item.id]) ? ', есть ответ' : ''}`}
            onClick={() => setIndex(position)}
          >
            {TASK_TRAITS[item.kind].mark ?? position + 1}
          </button>
        ))}
      </nav>

      <div className="runner__task">
        <p className="runner__eyebrow">
          Задание {index + 1} · {topicLabel(task.topic)}
        </p>
        <TaskView
          task={task}
          answer={answers[task.id]}
          disabled={locked}
          onChange={(answer) => changeAnswer(task, answer)}
          onPaste={() => void assessmentApi.signal(attempt.id, 'paste').catch(() => {})}
          attemptId={attempt.id}
          runsLeft={runsLeft}
          runnerAvailable={runnerAvailable}
          onRunsLeft={setRunsLeft}
        />
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
