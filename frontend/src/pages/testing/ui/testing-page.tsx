import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  ATTEMPT_STATUS_LABELS,
  AssessmentStatusBadge,
  TASK_KIND_LABELS,
  assessmentQueries,
  topicLabel,
} from '@/entities/assessment'
import type { AssessmentAttemptDto, AssessmentStatusDto } from '@/entities/assessment'
import { GRADE_LABELS, categoryQueries } from '@/entities/category'
import type { Grade } from '@/entities/category'
import { StartAssessmentForm } from '@/features/start-assessment'
import { formatDate, formatDateTime } from '@/shared/lib'
import { Page, QueryState, Section } from '@/shared/ui'
import { AssessmentRunner } from '@/widgets/assessment-runner'
import './testing-page.css'

const gradeLabel = (grade: string | null) => (grade ? (GRADE_LABELS[grade as Grade] ?? grade) : '')

/** Result of a finished attempt: the score against the pass mark and what went well or not. */
function AttemptResult({ attempt }: { attempt: AssessmentAttemptDto }) {
  const passed = attempt.status === 'passed'
  return (
    <div className={`test-result test-result--${passed ? 'passed' : 'failed'}`} role="status">
      <p className="test-result__title">
        {passed ? 'Тест пройден — категория подтверждена' : 'Тест не пройден'}
      </p>
      <p className="test-result__score">
        {attempt.score === null ? '—' : Math.round(attempt.score)} из 100
        <span> · проходной балл {attempt.passScore}</span>
      </p>
      {!passed && (
        <p className="test-result__note">
          Категория не присвоена. Повторить попытку можно после паузы — дата указана ниже.
        </p>
      )}
      {attempt.breakdown && attempt.breakdown.length > 0 && (
        <table className="test-table">
          <caption className="visually-hidden">Результат по темам</caption>
          <thead>
            <tr>
              <th scope="col">Тема</th>
              <th scope="col">Тип</th>
              <th scope="col">Заданий</th>
              <th scope="col">Результат</th>
            </tr>
          </thead>
          <tbody>
            {attempt.breakdown.map((item) => (
              <tr key={`${item.kind}:${item.topic}`}>
                <td>{topicLabel(item.topic)}</td>
                <td>{TASK_KIND_LABELS[item.kind]}</td>
                <td>{item.total}</td>
                <td>{Math.round(item.earned * 100)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

function Overview({
  status,
  result,
}: {
  status: AssessmentStatusDto
  result: AssessmentAttemptDto | null
}) {
  const dictionary = useQuery(categoryQueries.dictionary())
  const specialization =
    dictionary.data?.specializations.find((item) => item.code === status.specialization)?.label ??
    status.specialization
  const lastTried = status.history[0]

  return (
    <>
      {result && <AttemptResult attempt={result} />}

      <Section title="Ваш статус">
        <div className="test-status">
          <AssessmentStatusBadge status={status.status} score={status.score} />
          {status.status === 'passed' && (
            <p>
              {specialization} · {gradeLabel(status.grade)}
            </p>
          )}
        </div>
      </Section>

      <Section title={status.status === 'passed' ? 'Сменить грейд' : 'Пройти тест'}>
        {status.nextAttemptAt ? (
          <p className="test-note">
            Следующая попытка будет доступна {formatDateTime(status.nextAttemptAt)}.
          </p>
        ) : (
          <StartAssessmentForm
            defaultSpecialization={status.specialization ?? lastTried?.specialization}
            defaultGrade={status.grade ?? lastTried?.grade}
          />
        )}
      </Section>

      {status.history.length > 0 && (
        <Section title="История попыток">
          <table className="test-table">
            <thead>
              <tr>
                <th scope="col">Тест</th>
                <th scope="col">Дата</th>
                <th scope="col">Итог</th>
                <th scope="col">Балл</th>
              </tr>
            </thead>
            <tbody>
              {status.history.map((attempt) => (
                <tr key={attempt.id}>
                  <td>{attempt.title}</td>
                  <td>{formatDate(attempt.startedAt)}</td>
                  <td>{ATTEMPT_STATUS_LABELS[attempt.status]}</td>
                  <td>{attempt.score === null ? '—' : Math.round(attempt.score)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Section>
      )}
    </>
  )
}

/** Candidate's path to a category: pick specialization and grade, take the test, see the result. */
export function TestingPage() {
  const status = useQuery(assessmentQueries.status())
  const [result, setResult] = useState<AssessmentAttemptDto | null>(null)

  return (
    <Page title="Тестирование" lead="Категория подтверждается тестом, а не резюме">
      <QueryState query={status}>
        {(data) =>
          data.activeAttemptId ? (
            <AssessmentRunner
              attemptId={data.activeAttemptId}
              runnerAvailable={data.codeRunnerAvailable}
              onFinished={setResult}
            />
          ) : (
            <Overview status={data} result={result} />
          )
        }
      </QueryState>
    </Page>
  )
}
