import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router'
import { JOB_STATUS_LABELS, candidateQueries } from '@/entities/candidate'
import { invitationQueries } from '@/entities/invitation'
import { getErrorMessage } from '@/shared/api'
import { ROUTES } from '@/shared/config'
import { formatRubRange } from '@/shared/lib'
import { ButtonLink, ErrorState, Loader, Page, Panel } from '@/shared/ui'
import { isNotReady, NOT_READY } from '@/widgets/invitations-inbox'
import { isWaiting } from '../../lib/cabinet-data'
import { isNotFound } from '../../lib/is-not-found'
import { candidateTodos } from '../../lib/todos'
import { TodoList } from './todo-list'
import { WaitingList } from './waiting-list'

function yearsLabel(years: number): string {
  const tail = years % 10
  const tens = years % 100
  if (tail === 1 && tens !== 11) return `${years} год`
  if (tail >= 2 && tail <= 4 && (tens < 12 || tens > 14)) return `${years} года`
  return `${years} лет`
}

export function CandidateOverview() {
  const profile = useQuery(candidateQueries.mine())
  const invitations = useQuery({
    ...invitationQueries.list('incoming'),
    enabled: profile.isSuccess,
  })

  if (profile.isPending) {
    return (
      <Page className="page--inset" title="Обзор">
        <Loader />
      </Page>
    )
  }
  if (profile.isError && !isNotFound(profile.error)) {
    return (
      <Page className="page--inset" title="Обзор">
        <ErrorState
          message={getErrorMessage(profile.error)}
          onRetry={() => void profile.refetch()}
        />
      </Page>
    )
  }
  if (!profile.data) {
    return (
      <Page
        className="page--inset"
        title="Обзор"
        lead="Резюме, тест на грейд и связь с ФСП. После этого работодатели видят вас в подборке."
      >
        <ButtonLink to={ROUTES.profileResume}>Создать резюме</ButtonLink>
      </Page>
    )
  }

  const own = profile.data
  const waiting = (invitations.data?.items ?? []).filter(isWaiting)
  const fresh = waiting.filter((item) => item.status === 'sent').length
  const facts = [
    { label: 'Категория', value: own.category?.label ?? 'Не подтверждена' },
    { label: 'Статус', value: JOB_STATUS_LABELS[own.jobStatus] },
    { label: 'Город', value: own.city ?? 'Не указан' },
    {
      label: 'Зарплата',
      value: own.salaryExpectation
        ? `от ${formatRubRange(own.salaryExpectation, own.salaryExpectation)}`
        : 'Не указана',
    },
    {
      label: 'Опыт',
      value: own.noExperience
        ? 'Без опыта'
        : own.experienceYears !== null
          ? yearsLabel(own.experienceYears)
          : 'Не указан',
    },
  ]

  return (
    <div className="cabinet-grid">
      <section className="cabinet-col" aria-labelledby="cabinet-waiting">
        <header className="cabinet-heading">
          <h2 id="cabinet-waiting">
            Ждут ответа{' '}
            {invitations.isSuccess && <span className="cabinet-heading__count">{fresh}</span>}
          </h2>
          <Link className="cabinet-link-btn" to={ROUTES.profileInvitations}>
            Все приглашения
          </Link>
        </header>
        {invitations.isPending ? (
          <Loader />
        ) : isNotReady(invitations.error) ? (
          <p className="cabinet-muted cabinet-muted--plate">{NOT_READY}</p>
        ) : invitations.isError ? (
          <ErrorState
            message={getErrorMessage(invitations.error)}
            onRetry={() => void invitations.refetch()}
          />
        ) : (
          <WaitingList
            items={waiting}
            direction="incoming"
            emptyText="Сейчас ответа ничего не ждёт."
          />
        )}
      </section>
      <aside className="cabinet-col">
        <Panel className="panel--frame" title="Что сделать">
          <TodoList items={candidateTodos(own)} />
        </Panel>
        <Panel
          title="Профиль"
          action={
            <Link className="cabinet-link-btn" to={ROUTES.profileResume}>
              Изменить
            </Link>
          }
        >
          <dl className="mini-facts">
            {facts.map((fact) => (
              <div key={fact.label}>
                <dt>{fact.label}</dt>
                <dd>{fact.value}</dd>
              </div>
            ))}
          </dl>
        </Panel>
      </aside>
    </div>
  )
}
