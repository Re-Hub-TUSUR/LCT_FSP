import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router'
import { JOB_STATUS_LABELS, candidateQueries } from '@/entities/candidate'
import { getErrorMessage } from '@/shared/api'
import { ROUTES } from '@/shared/config'
import { formatRubRange } from '@/shared/lib'
import { ButtonLink, EmptyState, ErrorState, Loader, Page, Panel } from '@/shared/ui'
import { CompanyLikes, InvitationsBoard } from '@/widgets/invitations-inbox'
import { candidateTodos } from '../../lib/todos'
import { TodoList } from './todo-list'

function yearsLabel(years: number): string {
  const tail = years % 10
  const tens = years % 100
  if (tail === 1 && tens !== 11) return `${years} год`
  if (tail >= 2 && tail <= 4 && (tens < 12 || tens > 14)) return `${years} года`
  return `${years} лет`
}

export function CandidateOverview() {
  const profile = useQuery(candidateQueries.mine())

  if (profile.isPending) {
    return (
      <Page className="page--inset" title="Обзор">
        <Loader />
      </Page>
    )
  }
  if (profile.isError) {
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
          <h2 id="cabinet-waiting">Приглашения</h2>
        </header>
        <CompanyLikes />
        <InvitationsBoard
          direction="incoming"
          empty={
            <EmptyState title="Приглашений пока нет">
              <Link className="cabinet-link" to={ROUTES.feed}>
                Смотреть вакансии
              </Link>
            </EmptyState>
          }
        />
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
