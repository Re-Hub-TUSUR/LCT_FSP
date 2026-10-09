import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  TASK_KIND_COUNT_LABELS,
  assessmentApi,
  assessmentKeys,
  assessmentQueries,
} from '@/entities/assessment'
import type {
  AssessmentTemplateDto,
  AssessmentTrackDto,
  AttemptDetailDto,
  TaskKind,
} from '@/entities/assessment'
import { GRADES, GRADE_LABELS, categoryQueries } from '@/entities/category'
import type { Grade } from '@/entities/category'
import { getErrorMessage } from '@/shared/api'
import { formatDateTime } from '@/shared/lib'
import { Button, QueryState, SelectField } from '@/shared/ui'
import './start-assessment-form.css'

type Props = {
  /** Specializations the candidate has tried: each keeps its own cooldown. */
  tracks: AssessmentTrackDto[]
  /** False while the server cannot check code: tests with a code task do not start. */
  runnerAvailable: boolean
  /** Pre-selects what the candidate has already confirmed or tried. */
  defaultSpecialization?: string | null
  defaultGrade?: string | null
  onStarted?: (attempt: AttemptDetailDto) => void
}

/** A template written for the specialization wins over the general one of the grade. */
function templateFor(templates: AssessmentTemplateDto[], specialization: string, grade: string) {
  const ofGrade = templates.filter((template) => template.grade === grade)
  return (
    ofGrade.find((template) => template.specialization === specialization) ??
    ofGrade.find((template) => template.specialization === null)
  )
}

/** One step up; the top grade has none. */
const nextGrade = (grade: string): Grade | undefined => GRADES[GRADES.indexOf(grade as Grade) + 1]

const days = (count: number) => (count === 0 ? 'сразу' : `через ${count} дн.`)

/** Specialization and declared grade: the test confirms exactly this pair. */
export function StartAssessmentForm({
  tracks,
  runnerAvailable,
  defaultSpecialization,
  defaultGrade,
  onStarted,
}: Props) {
  const queryClient = useQueryClient()
  const dictionary = useQuery(categoryQueries.dictionary())
  const templates = useQuery(assessmentQueries.templates())
  const [specialization, setSpecialization] = useState(defaultSpecialization ?? '')
  const [grade, setGrade] = useState(defaultGrade ?? '')
  const [touched, setTouched] = useState(false)

  const start = useMutation({
    mutationFn: assessmentApi.start,
    onSuccess: (attempt) => {
      queryClient.setQueryData(assessmentKeys.attempt(attempt.id), attempt)
      void queryClient.invalidateQueries({ queryKey: assessmentKeys.status() })
      onStarted?.(attempt)
    },
  })

  const chosen = Boolean(specialization && grade)
  const template = chosen ? templateFor(templates.data ?? [], specialization, grade) : undefined
  const track = tracks.find((item) => item.specialization === specialization)
  // The grade a strong result recommended is not held back by the grade-change cooldown.
  const recommended = track?.recommendation?.grade === grade ? track.recommendation : null
  // After a failed try the pause holds back the same grade and the ones above it, not the lower
  // ones (a confirmed category keeps its own grade-change pause, which is not lifted).
  const lowerOpen =
    track?.status === 'failed' &&
    Boolean(track.failedGrade) &&
    GRADES.indexOf(grade as Grade) < GRADES.indexOf(track.failedGrade as Grade)
  const pausedUntil = recommended
    ? recommended.nextAttemptAt
    : lowerOpen
      ? null
      : track?.nextAttemptAt
  const needsRunner = Boolean(template?.tasks.code) && !runnerAvailable
  const blocked =
    Boolean(pausedUntil) || needsRunner || (chosen && templates.isSuccess && !template)

  const onSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setTouched(true)
    if (chosen && !blocked) start.mutate({ specialization, grade })
  }

  return (
    <QueryState query={dictionary}>
      {(data) => (
        <form className="start-test" noValidate onSubmit={onSubmit}>
          <div className="start-test__fields">
            <SelectField
              id="test-specialization"
              label="Специализация"
              value={specialization}
              error={touched && !specialization ? 'Выберите специализацию' : undefined}
              onChange={(e) => setSpecialization(e.target.value)}
            >
              <option value="">Не выбрана</option>
              {data.specializations.map((item) => (
                <option key={item.code} value={item.code}>
                  {item.label}
                </option>
              ))}
            </SelectField>
            <SelectField
              id="test-grade"
              label="Грейд, на который претендуете"
              value={grade}
              error={touched && !grade ? 'Выберите грейд' : undefined}
              onChange={(e) => setGrade(e.target.value)}
            >
              <option value="">Не выбран</option>
              {data.grades.map((item) => (
                <option key={item.code} value={item.code}>
                  {item.label}
                </option>
              ))}
            </SelectField>
          </div>

          {template ? (
            <ul className="start-test__rules">
              <li>
                Тест идёт {template.durationMinutes} минут:{' '}
                {(Object.entries(template.tasks) as [TaskKind, number][])
                  .map(([kind, count]) => `${TASK_KIND_COUNT_LABELS[kind]} — ${count}`)
                  .join(', ')}
                .
              </li>
              <li>Таймер запускается сразу и не ставится на паузу.</li>
              {template.tasks.code && (
                <li>Код можно запускать на открытых тестах; итог считается по закрытым.</li>
              )}
              <li>
                Проходной балл — {template.passScore} из 100. Если не набрать, категория не
                присваивается, повторить можно {days(template.retryDays)}.
              </li>
              {Boolean(template.quizMin) && (
                <li>
                  Нужно ответить верно не менее чем на {template.quizMin}% вопросов: баллы за код
                  этого не заменяют.
                </li>
              )}
              {template.isBeta && (
                <li>Тест в бета-версии: подтверждённый грейд будет помечен как предварительный.</li>
              )}
              <li>
                После сдачи сменить грейд в этой специализации можно{' '}
                {days(template.gradeChangeDays)}. Другие специализации это не задерживает.
              </li>
              {nextGrade(grade) && (
                <li>
                  При результате от {template.recommendScore} из 100 тест на{' '}
                  {GRADE_LABELS[nextGrade(grade)!]} откроется сразу, без этой паузы.
                </li>
              )}
            </ul>
          ) : (
            <p className="start-test__note">
              {chosen && templates.isSuccess
                ? 'Тест для этого грейда ещё не подготовлен.'
                : 'Выберите специализацию и грейд, чтобы увидеть условия теста.'}
            </p>
          )}

          {recommended && !pausedUntil && (
            <p className="start-test__note" role="status">
              Этот грейд рекомендован по итогам вашего прошлого теста и доступен без паузы.
            </p>
          )}
          {lowerOpen && !pausedUntil && (
            <p className="start-test__note" role="status">
              Грейд ниже, чем в прошлой попытке, можно пройти сразу, без паузы.
            </p>
          )}
          {pausedUntil && (
            <p className="start-test__note" role="status">
              По этой специализации следующая попытка будет доступна {formatDateTime(pausedUntil)}.
              {track?.failedGrade && track.status === 'failed'
                ? ' Тест грейда ниже и тест по другой специализации можно начать сейчас.'
                : ' Тест по другой специализации можно начать сейчас.'}
            </p>
          )}
          {needsRunner && (
            <p className="start-test__note" role="status">
              Проверка кода сейчас недоступна, поэтому тест с задачей на код начать нельзя.
              Попробуйте позже.
            </p>
          )}
          {start.isError && (
            <p className="start-test__error" role="alert">
              {getErrorMessage(start.error)}
            </p>
          )}

          <Button type="submit" size="inline" disabled={start.isPending || blocked}>
            {start.isPending ? 'Готовим вариант…' : 'Начать тест'}
          </Button>
        </form>
      )}
    </QueryState>
  )
}
