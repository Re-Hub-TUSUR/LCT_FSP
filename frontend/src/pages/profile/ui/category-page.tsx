import { useQuery } from '@tanstack/react-query'
import {
  ATTEMPT_STATUS_LABELS,
  AssessmentStatusBadge,
  assessmentQueries,
} from '@/entities/assessment'
import { candidateQueries } from '@/entities/candidate'
import { categoryQueries } from '@/entities/category'
import { useSession } from '@/entities/session'
import { ROUTES } from '@/shared/config'
import { getErrorMessage } from '@/shared/api'
import { formatDate, isInFuture } from '@/shared/lib'
import { Button, ButtonLink, DataRows, ErrorState, Loader, Page, Panel } from '@/shared/ui'
import { gradeLabel } from '../lib/cabinet-data'
import { RoleNote } from './role-note'

export function CategoryPage() {
  const { user } = useSession()
  const candidate = user?.role === 'candidate'
  const status = useQuery({ ...assessmentQueries.status(), enabled: candidate })
  const dictionary = useQuery({ ...categoryQueries.dictionary(), enabled: candidate })
  const profile = useQuery({ ...candidateQueries.mine(), enabled: candidate })

  if (!candidate) {
    return <RoleNote title="Категория" text="Категорию получает специалист после теста." />
  }
  if (status.isPending) {
    return (
      <Page className="page--inset" title="Категория и грейд">
        <Loader />
      </Page>
    )
  }
  if (status.isError) {
    return (
      <Page className="page--inset" title="Категория и грейд">
        <ErrorState message={getErrorMessage(status.error)} onRetry={() => void status.refetch()} />
      </Page>
    )
  }

  const data = status.data
  const passed = data.status === 'passed'
  const locked = Boolean(data.nextAttemptAt && isInFuture(data.nextAttemptAt))
  const specLabel = (code: string | null) =>
    dictionary.data?.specializations.find((item) => item.code === code)?.label ?? code ?? ''
  const primary = data.tracks.find((track) => track.isPrimary) ?? null
  const confirmedAt = data.history.find(
    (attempt) =>
      attempt.assignmentId === null &&
      attempt.status === 'passed' &&
      attempt.specialization === data.specialization,
  )?.finishedAt
  const visible = profile.data ? profile.data.jobStatus !== 'not_looking' : false
  const declared = profile.data && !profile.data.gradeVerified ? profile.data.category : null

  const path = [
    { id: 'resume', title: 'Резюме', done: Boolean(profile.data) },
    { id: 'test', title: 'Тест на грейд', done: passed || data.history.length > 0 },
    { id: 'category', title: 'Категория подтверждена', done: passed },
    { id: 'visible', title: 'Видна работодателям', done: passed && visible },
  ]
  const current = path.find((step) => !step.done)

  return (
    <Page
      className="page--inset"
      title="Категория и грейд"
      lead="Категория — специализация плюс грейд, который подтвердил тест. По ней работодатели находят вас в банке кандидатов."
    >
      <div className="cabinet-grid">
        <div className="cabinet-col">
          <Panel title="Ваша категория">
            <p className="cat-big">
              {passed && data.specialization ? (
                <>
                  {specLabel(data.specialization)}
                  {data.grade && <span className="cat-big__grade">{gradeLabel(data.grade)}</span>}
                </>
              ) : declared ? (
                <>
                  {declared.label}
                  <span className="cat-big__grade cat-big__grade--dim">не подтверждён</span>
                </>
              ) : (
                <span className="cat-big__empty">Категория ещё не подтверждена</span>
              )}
            </p>
            <div>
              <AssessmentStatusBadge status={data.status} score={data.score} />
            </div>
            <DataRows
              rows={[
                {
                  key: 'score',
                  label: 'Балл теста',
                  value: data.score != null ? `${Math.round(data.score)} / 100` : null,
                },
                ...(confirmedAt
                  ? [{ key: 'date', label: 'Подтверждена', value: formatDate(confirmedAt) }]
                  : []),
                {
                  key: 'visible',
                  label: 'В банке кандидатов',
                  value: passed
                    ? visible
                      ? 'Видна работодателям'
                      : 'Скрыта: вы не ищете работу'
                    : 'Появится после теста',
                },
              ]}
            />
          </Panel>

          <Panel title="Как вы получили категорию">
            <ol className="steps">
              {path.map((step, index) => (
                <li
                  key={step.id}
                  className={`steps__item${step.done ? ' is-done' : ''}${step.id === current?.id ? ' is-current' : ''}`}
                  aria-current={step.id === current?.id ? 'step' : undefined}
                >
                  <span className="steps__index" aria-hidden="true">
                    0{index + 1}
                  </span>
                  <span>
                    <span className="steps__title">{step.title}</span>
                    <span className="steps__state">
                      {step.done ? 'Готово' : step.id === current?.id ? 'Сейчас' : 'Дальше'}
                    </span>
                  </span>
                </li>
              ))}
            </ol>
          </Panel>

          <Panel title="История тестов">
            {data.history.length === 0 ? (
              <p className="cabinet-muted">Вы ещё не проходили тесты.</p>
            ) : (
              <div className="cat-table-wrap">
                <table className="cat-table">
                  <thead>
                    <tr>
                      <th scope="col">Дата</th>
                      <th scope="col">Тест</th>
                      <th scope="col">Итог</th>
                      <th scope="col">Балл</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.history.map((attempt) => (
                      <tr key={attempt.id}>
                        <td>{formatDate(attempt.finishedAt ?? attempt.startedAt)}</td>
                        <td>{attempt.title}</td>
                        <td>{ATTEMPT_STATUS_LABELS[attempt.status]}</td>
                        <td>{attempt.score != null ? Math.round(attempt.score) : '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Panel>
        </div>

        <div className="cabinet-col">
          <Panel title={passed ? 'Сменить грейд' : 'Подтвердить грейд'}>
            <p className="cabinet-muted">
              {passed
                ? locked && data.nextAttemptAt
                  ? `Новый тест на другой грейд — с ${formatDate(data.nextAttemptAt)}.`
                  : 'Можно пройти тест на другой грейд. Категория сменится, только если вы примете новый результат.'
                : 'Грейд выбирается только тестом: короткие задачи по вашей специализации.'}
            </p>
            {primary?.recommendation && (
              <p className="cabinet-muted">
                Сильный результат открыл грейд {gradeLabel(primary.recommendation.grade)}
                {primary.recommendation.nextAttemptAt &&
                isInFuture(primary.recommendation.nextAttemptAt)
                  ? ` — тест доступен с ${formatDate(primary.recommendation.nextAttemptAt)}.`
                  : ' — тест на него можно пройти без ожидания.'}
              </p>
            )}
            <div>
              {passed && locked && !primary?.recommendation ? (
                <Button size="inline" disabled>
                  Пройти тест на другой грейд
                </Button>
              ) : (
                <ButtonLink to={ROUTES.testing}>
                  {passed ? 'Пройти тест на другой грейд' : 'Пройти тест'}
                </ButtonLink>
              )}
            </div>
          </Panel>

          {data.tracks.length > 0 && (
            <Panel title="Специализации">
              <DataRows
                rows={data.tracks.map((track) => ({
                  key: track.specialization,
                  label: track.isPrimary ? 'Основная' : 'Ещё',
                  value: (
                    <>
                      {specLabel(track.specialization)}
                      {track.grade ? ` · ${gradeLabel(track.grade)}` : ''}
                    </>
                  ),
                  note: <AssessmentStatusBadge status={track.status} score={track.score} />,
                }))}
              />
            </Panel>
          )}
        </div>
      </div>
    </Page>
  )
}
