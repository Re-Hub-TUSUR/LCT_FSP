import { useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
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
import { ButtonLink, Page, QueryState, Section, Tag } from '@/shared/ui'
import { AssessmentRunner } from '@/widgets/assessment-runner'
import { AssignmentInbox } from '@/widgets/assignment-inbox'
import { AttemptInterview } from '@/widgets/attempt-interview'
import { AssignmentReview } from '@/widgets/assignment-review'
import './testing-page.css'

/** What the start form opens with. */
type Preset = { specialization: string; grade: string }

const gradeLabel = (grade: string | null) => (grade ? (GRADE_LABELS[grade as Grade] ?? grade) : '')

/** Result of a finished attempt: the score against the pass mark and what went well or not. */
function AttemptResult({
  attempt,
  onRecommended,
}: {
  attempt: AssessmentAttemptDto
  /** Puts the recommended test into the start form. */
  onRecommended: (preset: Preset) => void
}) {
  const passed = attempt.status === 'passed'
  // A test a company sent confirms nothing and starts no cooldown.
  const assigned = attempt.assignmentId !== null
  const { recommendedGrade, specialization } = attempt

  if (attempt.status === 'grading') {
    return (
      <div className="test-result" role="status">
        <p className="test-result__title">Проверяем решение</p>
        <p className="test-result__note">
          Ответы сохранены, но сервис проверки кода сейчас не отвечает. Итог появится в истории
          попыток, как только он вернётся; пауза за это время не начисляется.
        </p>
      </div>
    )
  }

  if (attempt.status === 'interview') {
    return (
      <div className="test-result" role="status">
        <p className="test-result__title">Тест сдан по баллам</p>
        <p className="test-result__note">
          Осталось собеседование с ИИ: 2–3 вопроса по вашему коду. Грейд подтвердится после ответов.
        </p>
      </div>
    )
  }

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
      {recommendedGrade && specialization && (
        <p className="test-result__note test-result__note--strong">
          Отличный результат — рекомендуем тест на {gradeLabel(recommendedGrade)}: он доступен уже
          сейчас, без паузы.{' '}
          <button
            type="button"
            className="test-link"
            onClick={() => onRecommended({ specialization, grade: recommendedGrade })}
          >
            Выбрать этот тест
          </button>
        </p>
      )}
      {!passed && !assigned && (
        <p className="test-result__note">
          Категория не присвоена. Повторить попытку по этой специализации можно после паузы — дата
          указана ниже; тест по другой специализации доступен сразу.
        </p>
      )}
      {attempt.breakdown && attempt.breakdown.length > 0 && (
        <div className="test-table-wrap">
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
        </div>
      )}
    </div>
  )
}

/** Confirmed and tried specializations: each has its own grade, cooldown and «primary» switch. */
function Tracks({
  status,
  onRecommended,
}: {
  status: AssessmentStatusDto
  onRecommended: (preset: Preset) => void
}) {
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
      <div className="test-table-wrap">
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
                <td>
                  {track.grade ? gradeLabel(track.grade) : 'Не подтверждён'}
                  {track.recommendation && (
                    <button
                      type="button"
                      className="test-link test-link--hint"
                      onClick={() =>
                        onRecommended({
                          specialization: track.specialization,
                          grade: track.recommendation!.grade,
                        })
                      }
                    >
                      Рекомендуем {gradeLabel(track.recommendation.grade)}
                    </button>
                  )}
                </td>
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
      </div>
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
  const primary = status.tracks.find((track) => track.isPrimary)
  const [preset, setPreset] = useState<Preset | null>(null)
  const startForm = useRef<HTMLDivElement>(null)

  const choose = (next: Preset) => {
    setPreset(next)
    startForm.current?.scrollIntoView?.({ behavior: 'smooth', block: 'start' })
  }

  return (
    <>
      {result && <AttemptResult attempt={result} onRecommended={choose} />}

      <AssignmentInbox />

      <Section title="Мои категории">
        <Tracks status={status} onRecommended={choose} />
      </Section>

      <div ref={startForm}>
        <Section title="Пройти тест">
          <StartAssessmentForm
            // A chosen recommendation reopens the form with it.
            key={preset ? `${preset.specialization}:${preset.grade}` : 'default'}
            tracks={status.tracks}
            runnerAvailable={status.codeRunnerAvailable}
            defaultSpecialization={
              preset?.specialization ?? status.specialization ?? lastTried?.specialization
            }
            defaultGrade={
              preset?.grade ?? primary?.recommendation?.grade ?? status.grade ?? lastTried?.grade
            }
          />
        </Section>
      </div>

      {status.history.length > 0 && (
        <Section title="История попыток">
          <div className="test-table-wrap">
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
          </div>
        </Section>
      )}
    </>
  )
}

/** Candidate's path to a category: pick specialization and grade, take the test, see the result. */
function CandidateTesting() {
  const queryClient = useQueryClient()
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
        ) : data.interviewAttemptId ? (
          // The grade of a test passed on points waits for the AI interview about its code.
          <AttemptInterview
            attemptId={data.interviewAttemptId}
            onDone={() => {
              setResult(null)
              void queryClient.invalidateQueries({ queryKey: assessmentKeys.status() })
            }}
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
          <ButtonLink variant="ghost" to={ROUTES.testBuilder}>
            Конструктор тестов →
          </ButtonLink>
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
