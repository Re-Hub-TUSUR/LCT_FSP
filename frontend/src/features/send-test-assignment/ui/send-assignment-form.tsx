import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router'
import { assignmentApi, assignmentKeys, bankQueries } from '@/entities/assessment'
import { getErrorMessage } from '@/shared/api'
import { ROUTES } from '@/shared/config'
import { addDays, fromDateTimeInputs, toDateInput } from '@/shared/lib'
import { Button, QueryState, SelectField, TextArea, TextField } from '@/shared/ui'
import './send-assignment-form.css'

const DEFAULT_DUE_DAYS = 7

type Props = {
  candidateId: string
  /** Mutual interest: the server refuses to send a test without it. */
  matched: boolean
}

/** Employer sends one of the company's own tests to a matched candidate. */
export function SendAssignmentForm({ candidateId, matched }: Props) {
  const queryClient = useQueryClient()
  const tests = useQuery({ ...bankQueries.tests('employer'), enabled: matched })
  const [testId, setTestId] = useState('')
  const [due, setDue] = useState(() => toDateInput(addDays(new Date(), DEFAULT_DUE_DAYS)))
  const [message, setMessage] = useState('')
  const [problem, setProblem] = useState('')

  const send = useMutation({
    mutationFn: assignmentApi.send,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: assignmentKeys.outgoing() })
      setMessage('')
    },
  })

  if (!matched) {
    return (
      <p className="send-test__note">
        Тестовое можно отправить после взаимного интереса: добавьте кандидата в избранное и
        дождитесь, пока он отметит одну из ваших вакансий.
      </p>
    )
  }

  const onSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    // The candidate may start until the end of the chosen day.
    const dueAt = fromDateTimeInputs(due, '23:59')
    if (!testId) return setProblem('Выберите тест')
    if (!dueAt || dueAt <= new Date()) return setProblem('Срок должен быть в будущем')
    setProblem('')
    send.mutate({
      testId,
      candidateId,
      dueAt: dueAt.toISOString(),
      message: message.trim() || null,
    })
  }

  return (
    <QueryState query={tests}>
      {(items) => {
        const active = items.filter((test) => test.isActive)
        if (active.length === 0) {
          return (
            <p className="send-test__note">
              У компании пока нет активных тестов. Соберите тест из своих задач в{' '}
              <Link to={ROUTES.testBuilder}>конструкторе тестов</Link>.
            </p>
          )
        }
        return (
          <form className="send-test" noValidate onSubmit={onSubmit}>
            <div className="send-test__row">
              <SelectField
                id="assignment-test"
                label="Тест"
                value={testId}
                onChange={(e) => setTestId(e.target.value)}
              >
                <option value="">Не выбран</option>
                {active.map((test) => (
                  <option key={test.id} value={test.id}>
                    {test.title} · {test.durationMinutes} мин
                  </option>
                ))}
              </SelectField>
              <TextField
                id="assignment-due"
                label="Начать не позже"
                type="date"
                value={due}
                onChange={(e) => setDue(e.target.value)}
              />
            </div>
            <TextArea
              id="assignment-message"
              label="Сообщение кандидату"
              placeholder="Что это за задание и что будет дальше"
              maxLength={2000}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
            />

            {(problem || send.isError) && (
              <p className="send-test__status send-test__status--error" role="alert">
                {problem || getErrorMessage(send.error)}
              </p>
            )}
            {send.isSuccess && !problem && (
              <p className="send-test__status" role="status">
                Тестовое отправлено. Результат появится в разделе{' '}
                <Link to={ROUTES.testing}>«Тестовые»</Link>.
              </p>
            )}

            <Button type="submit" size="inline" disabled={send.isPending}>
              {send.isPending ? 'Отправляем…' : 'Отправить тестовое'}
            </Button>
          </form>
        )
      }}
    </QueryState>
  )
}
