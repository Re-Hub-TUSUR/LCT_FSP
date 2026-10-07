import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router'
import { companyQueries } from '@/entities/company'
import type { CompanyDto } from '@/entities/company'
import { invitationQueries } from '@/entities/invitation'
import { verificationQueries } from '@/features/company-verification'
import type { VerificationStatus } from '@/features/company-verification'
import { getErrorMessage } from '@/shared/api'
import { ROUTES } from '@/shared/config'
import { ButtonLink, ErrorState, Loader, Page, Panel, StatusTag } from '@/shared/ui'
import { isNotReady, NOT_READY } from '@/widgets/invitations-inbox'
import { isWaiting } from '../../lib/cabinet-data'
import { isNotFound } from '../../lib/is-not-found'
import { TodoList } from './todo-list'
import type { TodoItem } from './todo-list'
import { WaitingList } from './waiting-list'

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

function todosOf(company: CompanyDto, invited: boolean): TodoItem[] {
  return [
    {
      id: 'legal',
      label: 'Заполнить реквизиты',
      done: Boolean(company.inn && company.ogrn && company.legalAddress),
      to: ROUTES.profileCompany,
    },
    {
      id: 'profile',
      label: 'Описать компанию для кандидатов',
      done: Boolean(company.description && company.website),
      to: ROUTES.profileCompany,
    },
    { id: 'logo', label: 'Загрузить логотип', done: company.hasLogo, to: ROUTES.profileCompany },
    {
      id: 'accreditation',
      label: 'Подтвердить IT-аккредитацию',
      done: company.itAccredited,
      to: ROUTES.profileCompany,
    },
    { id: 'invite', label: 'Пригласить первого кандидата', done: invited, to: ROUTES.feed },
  ]
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
  if (company.isError && !isNotFound(company.error)) {
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
  const waiting = items.filter(isWaiting)
  const accepted = items.filter((item) => item.status === 'accepted').length
  const facts = [
    { label: 'ИНН', value: own.inn ?? 'Не указан' },
    { label: 'Город', value: own.city ?? 'Не указан' },
    { label: 'Отрасль', value: own.industry ?? 'Не указана' },
    { label: 'Приглашений', value: invitations.isSuccess ? String(items.length) : '—' },
    { label: 'Приняли', value: invitations.isSuccess ? String(accepted) : '—' },
  ]

  return (
    <Page
      className="page--inset"
      title={own.name}
      lead={
        waiting.length > 0
          ? `Ждут ответа кандидатов: ${waiting.length}. Контакты откроются после согласия.`
          : 'Найдите кандидатов в банке и отправьте предложение с зарплатой.'
      }
      actions={<ButtonLink to={ROUTES.feed}>Открыть банк кандидатов</ButtonLink>}
    >
      <div className="cabinet-grid">
        <div className="cabinet-col">
          <Panel
            title="Ждут ответа кандидатов"
            action={
              <Link className="cabinet-link-btn" to={ROUTES.profileInvitations}>
                Все приглашения
              </Link>
            }
          >
            {invitations.isPending ? (
              <Loader />
            ) : isNotReady(invitations.error) ? (
              <p className="cabinet-muted">{NOT_READY}</p>
            ) : invitations.isError ? (
              <ErrorState
                message={getErrorMessage(invitations.error)}
                onRetry={() => void invitations.refetch()}
              />
            ) : (
              <WaitingList
                items={waiting}
                direction="outgoing"
                emptyText="Все кандидаты ответили — или приглашений ещё не было."
              />
            )}
          </Panel>
        </div>
        <div className="cabinet-col">
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
          <Panel title="Что сделать">
            <TodoList items={todosOf(own, items.length > 0)} />
          </Panel>
        </div>
      </div>
    </Page>
  )
}
