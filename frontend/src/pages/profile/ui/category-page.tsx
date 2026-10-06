import { useQuery } from '@tanstack/react-query'
import {
  ATTEMPT_STATUS_LABELS,
  AssessmentStatusBadge,
  assessmentQueries,
} from '@/entities/assessment'
import { GRADE_LABELS, categoryQueries } from '@/entities/category'
import type { Grade } from '@/entities/category'
import { useSession } from '@/entities/session'
import { ROUTES } from '@/shared/config'
import { getErrorMessage } from '@/shared/api'
import { formatDate, isInFuture } from '@/shared/lib'
import { Button, ButtonLink, ErrorState, Loader, Page } from '@/shared/ui'
import { RoleNote } from './role-note'

export function CategoryPage() {
  const { user } = useSession()
  const status = useQuery({
    ...assessmentQueries.status(),
    enabled: user?.role === 'candidate',
  })
  const dictionary = useQuery({
    ...categoryQueries.dictionary(),
    enabled: user?.role === 'candidate',
  })

  if (user?.role !== 'candidate') {
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
  const locked = Boolean(data.nextAttemptAt && isInFuture(data.nextAttemptAt))
  const specLabel = (code: string | null) =>
    dictionary.data?.specializations.find((item) => item.code === code)?.label ?? code

  return (
    <Page
      className="page--inset"
      title="Категория и грейд"
      lead="Категория — специализация плюс грейд, который вы приняли после теста."
      actions={
        data.status === 'passed' && locked ? (
          <Button size="inline" disabled>
            Пройти тест на другой грейд
          </Button>
        ) : (
          <ButtonLink to={ROUTES.testing}>
            {data.status === 'passed' ? 'Пройти тест на другой грейд' : 'Пройти тест'}
          </ButtonLink>
        )
      }
    >
      <p className="cabinet-copy">
        <AssessmentStatusBadge status={data.status} score={data.score} />
        {data.status === 'passed' && data.specialization && (
          <>
            {' '}
            {specLabel(data.specialization)}
            {data.grade ? ` · ${GRADE_LABELS[data.grade as Grade] ?? data.grade}` : ''}
          </>
        )}
      </p>
      {locked && data.nextAttemptAt && (
        <p className="cabinet-copy">Сменить грейд можно с {formatDate(data.nextAttemptAt)}.</p>
      )}
      {data.tracks.length > 0 && (
        <ul className="history">
          {data.tracks.map((track) => (
            <li key={track.specialization} className="history__item">
              <span>{specLabel(track.specialization)}</span>
              <span className="history__meta">
                <AssessmentStatusBadge status={track.status} score={track.score} />
                {track.grade ? ` · ${GRADE_LABELS[track.grade as Grade] ?? track.grade}` : ''}
                {track.isPrimary ? ' · основная' : ''}
              </span>
            </li>
          ))}
        </ul>
      )}
      {data.history.length > 0 && (
        <ul className="history">
          {data.history.map((attempt) => (
            <li key={attempt.id} className="history__item">
              <span>{attempt.title}</span>
              <span className="history__meta">
                {formatDate(attempt.finishedAt ?? attempt.startedAt)} ·{' '}
                {ATTEMPT_STATUS_LABELS[attempt.status]}
                {attempt.score != null ? ` · ${Math.round(attempt.score)} / 100` : ''}
              </span>
            </li>
          ))}
        </ul>
      )}
    </Page>
  )
}
