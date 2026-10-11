import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router'
import { companyQueries } from '@/entities/company'
import { invitationQueries } from '@/entities/invitation'
import { verificationQueries } from '@/features/company-verification'
import type { VerificationStatus } from '@/features/company-verification'
import { getErrorMessage } from '@/shared/api'
import { ROUTES } from '@/shared/config'
import { ButtonLink, EmptyState, ErrorState, Loader, Page, Panel, StatusTag } from '@/shared/ui'
import { InvitationsBoard } from '@/widgets/invitations-inbox'
import { employerTodos } from '../../lib/todos'
import { TodoList } from './todo-list'

function AccreditationTag({
  accredited,
  status,
}: {
  accredited: boolean
  status: VerificationStatus | null | undefined
}) {
  if (accredited) return <StatusTag tone="done">Подтверждена</StatusTag>
  if (status === 'pending') return <StatusTag tone="wait">На проверке</StatusTag>
  if (status === 'rejected') return <StatusTag tone="off">Отклонена</StatusTag>
  return <StatusTag tone="todo">Не подана</StatusTag>
}

export function EmployerOverview() {
  const company = useQuery(companyQueries.mine())
  const invitations = useQuery({
    ...invitationQueries.list('outgoing'),
    enabled: company.isSuccess,
  })
  const verification = useQuery({
    ...verificationQueries.mine(),
    enabled: company.isSuccess && !company.data?.itAccredited,
  })

  if (company.isPending) {
    return (
      <Page className="page--inset" title="Обзор">
        <Loader />
      </Page>
    )
  }
  if (company.isError) {
    return (
      <Page className="page--inset" title="Обзор">
        <ErrorState
          message={getErrorMessage(company.error)}
          onRetry={() => void company.refetch()}
        />
      </Page>
    )
  }
  if (!company.data) {
    return (
      <Page
        className="page--inset"
        title="Обзор"
        lead="Реквизиты и профиль компании. Без этого приглашения недоступны."
      >
        <ButtonLink to={ROUTES.profileCompany}>Заполнить профиль компании</ButtonLink>
      </Page>
    )
  }

  const own = company.data
  const items = invitations.data?.items ?? []
  const accepted = items.filter((item) => item.status === 'accepted').length
  const facts = [
    { label: 'ИНН', value: own.inn ?? 'Не указан' },
    { label: 'Город', value: own.city ?? 'Не указан' },
    { label: 'Отрасль', value: own.industry ?? 'Не указана' },
    { label: 'Приглашений', value: invitations.isSuccess ? String(items.length) : '—' },
    { label: 'Приняли', value: invitations.isSuccess ? String(accepted) : '—' },
  ]

  const todos = employerTodos(own, items.length > 0)

  return (
    <div className="cabinet-grid">
      <section className="cabinet-col" aria-labelledby="cabinet-waiting">
        <header className="cabinet-heading">
          <h2 id="cabinet-waiting">Приглашения</h2>
        </header>
        <InvitationsBoard
          direction="outgoing"
          empty={
            <EmptyState title="Вы ещё никого не пригласили">
              <Link className="cabinet-link" to={ROUTES.feed}>
                Открыть банк кандидатов
              </Link>
            </EmptyState>
          }
        />
      </section>
      <aside className="cabinet-col">
        <Panel
          className="panel--frame"
          title="Что сделать"
          action={
            <span className="cabinet-progress">
              {todos.filter((item) => item.done).length}/{todos.length}
            </span>
          }
        >
          <TodoList items={todos} />
        </Panel>
        <Panel
          title="Компания"
          action={
            <Link className="cabinet-link-btn" to={ROUTES.profileCompany}>
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
            <div>
              <dt>IT-аккредитация</dt>
              <dd>
                <AccreditationTag
                  accredited={own.itAccredited}
                  status={verification.data?.status}
                />
              </dd>
            </div>
          </dl>
        </Panel>
      </aside>
    </div>
  )
}
