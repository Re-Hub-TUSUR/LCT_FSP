import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { assessmentApi, assessmentKeys, assessmentQueries } from '@/entities/assessment'
import type { InterviewDto, InterviewResultDto } from '@/entities/assessment'
import { getErrorMessage } from '@/shared/api'
import { Button, QueryState, Section, TextArea } from '@/shared/ui'
import './attempt-interview.css'

const MAX_ANSWER = 2000

function clock(milliseconds: number) {
  const total = Math.max(0, Math.ceil(milliseconds / 1000))
  return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, '0')}`
}

type Props = {
  attemptId: string
  /** The candidate leaves the result: the page shows the categories again. */
  onDone: () => void
}

/**
 * AI interview after a grade test: the test passed on points and the code works, now 2–3
 * questions about that code show whether the candidate understands it. The grade is confirmed
 * only after the answers are marked.
 */
export function AttemptInterview({ attemptId, onDone }: Props) {
  const query = useQuery(assessmentQueries.interview(attemptId))

  return (
    <Section title="Собеседование с ИИ">
      <QueryState query={query} loadingLabel="Готовим вопросы по вашему коду…">
        {(interview) =>
          interview.result ? (
            <InterviewOutcome interview={interview} result={interview.result} onDone={onDone} />
          ) : (
            <InterviewQuestions interview={interview} />
          )
        }
      </QueryState>
    </Section>
  )
}

function InterviewQuestions({ interview }: { interview: InterviewDto }) {
  const queryClient = useQueryClient()
  const [answers, setAnswers] = useState<string[]>(() => interview.questions.map(() => ''))
  const [now, setNow] = useState(() => Date.now())
  const left = interview.deadline ? new Date(interview.deadline).getTime() - now : null
  const timeUp = left !== null && left <= 0

  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 1000)
    return () => window.clearInterval(timer)
  }, [])

  const submit = useMutation({
    mutationFn: () => assessmentApi.answerInterview(interview.attemptId, answers),
    // The categories refresh when the candidate leaves the result, not under it.
    onSuccess: (next) => queryClient.setQueryData(assessmentKeys.interview(next.attemptId), next),
  })

  // When the time runs out the answers go as they are.
  const { mutate: submitNow, isIdle } = submit
  useEffect(() => {
    if (timeUp && isIdle) submitNow()
  }, [timeUp, isIdle, submitNow])

  const blank = answers.some((answer) => !answer.trim())

  return (
    <div className="interview">
      <p className="interview__lead">
        Тест сдан по баллам, закрытые тесты вашего кода пройдены. Чтобы подтвердить грейд, ответьте
        своими словами на вопросы о решении — как на собеседовании.
      </p>
      {left !== null && (
        <p className="interview__clock">
          Осталось <span>{clock(left)}</span>
        </p>
      )}
      <ol className="interview__questions">
        {interview.questions.map((question, index) => (
          <li key={question.number} className="interview__question">
            <p className="interview__task">Задача «{question.taskTitle}»</p>
            <p className="interview__text" id={`interview-question-${question.number}`}>
              {question.text}
            </p>
            <TextArea
              id={`interview-answer-${question.number}`}
              label={`Ответ на вопрос ${question.number}`}
              hideLabel
              aria-describedby={`interview-question-${question.number}`}
              rows={4}
              maxLength={MAX_ANSWER}
              value={answers[index] ?? ''}
              disabled={submit.isPending || timeUp}
              onChange={(event) => {
                const value = event.target.value
                setAnswers((prev) => prev.map((item, i) => (i === index ? value : item)))
              }}
            />
          </li>
        ))}
      </ol>
      {submit.isError && (
        <p className="interview__error" role="alert">
          {getErrorMessage(submit.error)}
        </p>
      )}
      <Button size="inline" disabled={submit.isPending || blank} onClick={() => submit.mutate()}>
        {submit.isPending ? 'Оцениваем ответы…' : 'Отправить ответы'}
      </Button>
    </div>
  )
}

function InterviewOutcome({
  interview,
  result,
  onDone,
}: {
  interview: InterviewDto
  result: InterviewResultDto
  onDone: () => void
}) {
  const question = (number: number) => interview.questions.find((item) => item.number === number)

  return (
    <div
      className={`interview-result interview-result--${result.passed ? 'passed' : 'failed'}`}
      role="status"
    >
      <p className="interview-result__title">
        {result.passed ? 'Понимание кода подтверждено — грейд подтверждён' : 'Грейд не подтверждён'}
      </p>
      {result.score !== null && (
        <p className="interview-result__score">
          {Math.round(result.score)} из 100 <span>· проходной балл {result.passScore}</span>
        </p>
      )}
      {result.summary && <p className="interview-result__note">{result.summary}</p>}
      {result.marks.length > 0 && (
        <ol className="interview-result__marks">
          {result.marks.map((mark) => (
            <li key={mark.number}>
              <p className="interview-result__question">{question(mark.number)?.text}</p>
              <p className="interview-result__note">
                {mark.score} из 100{mark.comment ? ` — ${mark.comment}` : ''}
              </p>
            </li>
          ))}
        </ol>
      )}
      {!result.passed && (
        <p className="interview-result__note">
          Повторить тест по этой специализации можно после паузы — дата появится в «Моих
          категориях».
        </p>
      )}
      <Button size="inline" onClick={onDone}>
        К тестам
      </Button>
    </div>
  )
}
