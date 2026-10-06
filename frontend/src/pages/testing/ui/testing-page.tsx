import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router'
import {
  ATTEMPT_STATUS_LABELS,
  TASK_KIND_LABELS,
  assessmentApi,
  assessmentKeys,
  assessmentQueries,
  topicLabel,
} from '@/entities/assessment'
import type { AssessmentAttemptDto, AssessmentStatusDto } from '@/entities/assessment'
import { GRADE_LABELS, categoryQueries } from '@/entities/category'
import { useSession } from '@/entities/session'
import type { Grade } from '@/entities/category'
import { StartAssessmentForm } from '@/features/start-assessment'
import { getErrorMessage } from '@/shared/api'
import { formatDate } from '@/shared/lib'
import { ROUTES } from '@/shared/config'
import { Page, QueryState, Section, Tag } from '@/shared/ui'
import { AssessmentRunner } from '@/widgets/assessment-runner'
import { AssignmentInbox } from '@/widgets/assignment-inbox'
import { AssignmentReview } from '@/widgets/assignment-review'
import './testing-page.css'

const gradeLabel = (grade: string | null) => (grade ? (GRADE_LABELS[grade as Grade] ?? grade) : '')

/** Result of a finished attempt: the score against the pass mark and what went well or not. */
function AttemptResult({ attempt }: { attempt: AssessmentAttemptDto }) {
  const passed = attempt.status === 'passed'
  // A test a company sent confirms nothing and starts no cooldown.
  const assigned = attempt.assignmentId !== null

  if (attempt.status === 'awaiting_review') {
    return (
      <div className="test-result" role="status">
        <p className="test-result__title">Ответы отправлены</p>
        <p className="test-result__note">
          В тесте есть открытые вопросы: их проверяет компания. Итог появится в списке тестовых,
          когда она выставит оценки.
        </p>
      </div>
    )
  }

  return (
    <div className={`test-result test-result--${passed ? 'passed' : 'failed'}`} role="status">
      <p className="test-result__title">
        {assigned
          ? passed
            ? 'Тестовое пройдено'
            : 'Тестовое не пройдено'
          : passed
            ? 'Тест пройден — категория подтверждена'
            : 'Тест не пройден'}
      </p>
      <p className="test-result__score">
        {attempt.score === null ? '—' : Math.round(attempt.score)} из 100
        <span> · проходной балл {attempt.passScore}</span>
      </p>
      {!passed && !assigned && (
        <p className="test-result__note">
          Категория не присвоена. Повторить попытку по этой специализации можно после паузы — дата
          указана ниже; тест по другой специализации доступен сразу.
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

/** Confirmed and tried specializations: each has its own grade, cooldown and «primary» switch. */
function Tracks({ status }: { status: AssessmentStatusDto }) {
  const queryClient = useQueryClient()
  const dictionary = useQuery(categoryQueries.dictionary())
  const setPrimary = useMutation({
    mutationFn: assessmentApi.setPrimary,
    onSuccess: (next) => queryClient.setQueryData(assessmentKeys.status(), next),
  })
  const label = (code: string) =>
    dictionary.data?.specializations.find((item) => item.code === code)?.label ?? code

  if (status.tracks.length === 0) {
    return <p className="test-note">Подтверждённых категорий пока нет — пройдите первый тест.</p>
  }

  return (
    <>
      <table className="test-table">
        <thead>
          <tr>
            <th scope="col">Специализация</th>
            <th scope="col">Грейд</th>
            <th scope="col">Балл</th>
            <th scope="col">Следующая попытка</th>
            <th scope="col">Видят работодатели</th>
          </tr>
        </thead>
        <tbody>
          {status.tracks.map((track) => (
            <tr key={track.specialization}>
              <td>{label(track.specialization)}</td>
              <td>{track.grade ? gradeLabel(track.grade) : 'Не подтверждён'}</td>
              <td>{track.score === null ? '—' : Math.round(track.score)}</td>
              <td>{track.nextAttemptAt ? formatDate(track.nextAttemptAt) : 'Доступна'}</td>
              <td>
                {track.isPrimary ? (
                  <Tag>Основная</Tag>
                ) : track.status === 'passed' ? (
                  <button
                    type="button"
                    className="test-link"
                    disabled={setPrimary.isPending}
                    onClick={() => setPrimary.mutate(track.specialization)}
                  >
                    Сделать основной
                  </button>
                ) : (
                  '—'
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {setPrimary.isError && (
        <p className="test-note test-note--error" role="alert">
          {getErrorMessage(setPrimary.error)}
        </p>
      )}
    </>
  )
}

function Overview({
  status,
  result,
}: {
  status: AssessmentStatusDto
  result: AssessmentAttemptDto | null
}) {
  const lastTried = status.history[0]

  return (
    <>
      {result && <AttemptResult attempt={result} />}

      <AssignmentInbox />

      <Section title="Мои категории">
        <Tracks status={status} />
      </Section>

      <Section title="Пройти тест">
        <StartAssessmentForm
          tracks={status.tracks}
          runnerAvailable={status.codeRunnerAvailable}
          defaultSpecialization={status.specialization ?? lastTried?.specialization}
          defaultGrade={status.grade ?? lastTried?.grade}
        />
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
function CandidateTesting() {
  const status = useQuery(assessmentQueries.status())
  const [result, setResult] = useState<AssessmentAttemptDto | null>(null)

  return (
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
  )
}

/**
 * Candidates confirm their categories and take tests companies sent; employers follow the
 * tests they sent and grade open answers.
 */
export function TestingPage() {
  const { user } = useSession()

  if (user?.role === 'employer') {
    return (
      <Page
        title="Тестовые"
        lead="Тесты компании, отправленные кандидатам"
        actions={
          <Link className="feed__link" to={ROUTES.testBuilder}>
            Конструктор тестов →
          </Link>
        }
      >
        <AssignmentReview />
      </Page>
    )
  }

  return (
    <Page title="Тестирование" lead="Категория подтверждается тестом, а не резюме">
      <CandidateTesting />
    </Page>
  )
}
