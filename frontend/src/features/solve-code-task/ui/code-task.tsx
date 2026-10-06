import { useEffect, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { VERDICT_LABELS, assessmentApi } from '@/entities/assessment'
import type { CodeAnswerDto, CodeTaskDto, RunResultDto } from '@/entities/assessment'
import { getErrorMessage } from '@/shared/api'
import { Button, CodeEditor, SelectField } from '@/shared/ui'
import { starterFor } from '../config/starters'
import './code-task.css'

/** The server refuses runs more often than this; the button simply waits it out. */
const RUN_COOLDOWN_MS = 5000

type Props = {
  attemptId: string
  task: CodeTaskDto
  /** Null until the candidate picks a language or types anything. */
  answer: CodeAnswerDto | null
  runsLeft: number
  /** False while the code runner is not configured on the server. */
  runnerAvailable: boolean
  disabled?: boolean
  onChange: (answer: CodeAnswerDto) => void
  onRunsLeft: (runsLeft: number) => void
  /** Reported for reviewers; never changes the score. */
  onPaste?: () => void
}

/** Statement, editor and "Run" on the open tests. Hidden tests run only when the test ends. */
export function CodeTask({
  attemptId,
  task,
  answer,
  runsLeft,
  runnerAvailable,
  disabled,
  onChange,
  onRunsLeft,
  onPaste,
}: Props) {
  const { languages, samples, timeLimit } = task.content
  const language = answer?.language ?? languages[0]?.id ?? ''
  const code = answer?.code ?? starterFor(language)
  const [results, setResults] = useState<RunResultDto[] | null>(null)
  const [coolingDown, setCoolingDown] = useState(false)

  const run = useMutation({
    mutationFn: () => assessmentApi.run(attemptId, { taskId: task.id, language, code }),
    onSuccess: (response) => {
      setResults(response.results)
      onRunsLeft(response.runsLeft)
    },
    onSettled: () => setCoolingDown(true),
  })

  useEffect(() => {
    if (!coolingDown) return
    const timer = setTimeout(() => setCoolingDown(false), RUN_COOLDOWN_MS)
    return () => clearTimeout(timer)
  }, [coolingDown])

  const changeLanguage = (next: string) => {
    // An untouched starter follows the language; real code is never replaced.
    const untouched = answer === null || answer.code === starterFor(answer.language)
    onChange({ language: next, code: untouched ? starterFor(next) : code })
  }

  const canRun = runnerAvailable && !disabled && !run.isPending && !coolingDown && runsLeft > 0

  return (
    <div className="code-task">
      <div className="code-task__brief">
        <h2 className="code-task__title">{task.title}</h2>
        <p className="code-task__statement">{task.statement}</p>
        <p className="code-task__limit">Ограничение времени: {timeLimit} с на запуск</p>

        {samples.map((sample, index) => (
          // Samples are a fixed list of the task and never reorder.
          // oxlint-disable-next-line react/no-array-index-key
          <div key={index} className="code-task__sample">
            <div>
              <p className="code-task__label">Ввод</p>
              <pre>{sample.input}</pre>
            </div>
            <div>
              <p className="code-task__label">Ожидаемый вывод</p>
              <pre>{sample.expected}</pre>
            </div>
          </div>
        ))}
      </div>

      <div className="code-task__work">
        <SelectField
          id={`language-${task.id}`}
          label="Язык"
          value={language}
          disabled={disabled}
          onChange={(e) => changeLanguage(e.target.value)}
        >
          {languages.map((item) => (
            <option key={item.id} value={item.id}>
              {item.label}
            </option>
          ))}
        </SelectField>

        <CodeEditor
          value={code}
          language={language}
          label={`Решение задачи «${task.title}»`}
          readOnly={disabled}
          onChange={(value) => onChange({ language, code: value })}
          onPaste={onPaste}
        />

        <div className="code-task__actions">
          <Button variant="ghost" size="inline" disabled={!canRun} onClick={() => run.mutate()}>
            {run.isPending ? 'Выполняется…' : 'Запустить на открытых тестах'}
          </Button>
          <span className="code-task__runs">Осталось запусков: {runsLeft}</span>
        </div>

        {!runnerAvailable && (
          <p className="code-task__note" role="status">
            Сервис проверки кода сейчас не подключён: запустить решение и завершить тест с ним не
            получится. Сообщите организаторам.
          </p>
        )}
        {run.isError && (
          <p className="code-task__error" role="alert">
            {getErrorMessage(run.error)}
          </p>
        )}

        {results && (
          <ul className="code-task__results" aria-live="polite">
            {results.map((result, index) => (
              // Results mirror the fixed order of the open tests.
              // oxlint-disable-next-line react/no-array-index-key
              <li key={index} className="code-task__result">
                <p
                  className={`code-task__verdict code-task__verdict--${result.verdict === 'ok' ? 'ok' : 'fail'}`}
                >
                  Тест {index + 1}: {result.verdict ? VERDICT_LABELS[result.verdict] : 'выполнен'}
                  {result.time !== null && ` · ${result.time.toFixed(2)} с`}
                </p>
                {result.verdict !== 'ok' && (
                  <div className="code-task__sample">
                    <div>
                      <p className="code-task__label">Ваш вывод</p>
                      <pre>{result.output || '—'}</pre>
                    </div>
                    {result.error && (
                      <div>
                        <p className="code-task__label">Сообщение об ошибке</p>
                        <pre>{result.error}</pre>
                      </div>
                    )}
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
