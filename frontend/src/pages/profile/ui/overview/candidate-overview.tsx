import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router'
import { JOB_STATUS_LABELS, candidateQueries } from '@/entities/candidate'
import type { OwnCandidateDto } from '@/entities/candidate'
import { invitationQueries } from '@/entities/invitation'
import { getErrorMessage } from '@/shared/api'
import { ROUTES } from '@/shared/config'
import { formatRubRange } from '@/shared/lib'
import { ButtonLink, ErrorState, Loader, Page, Panel } from '@/shared/ui'
import { isNotReady, NOT_READY } from '@/widgets/invitations-inbox'
import { isWaiting } from '../../lib/cabinet-data'
import { isNotFound } from '../../lib/is-not-found'
import { TodoList } from './todo-list'
import type { TodoItem } from './todo-list'
import { WaitingList } from './waiting-list'

function yearsLabel(years: number): string {
  const tail = years % 10
  const tens = years % 100
  if (tail === 1 && tens !== 11) return `${years} год`
  if (tail >= 2 && tail <= 4 && (tens < 12 || tens > 14)) return `${years} года`
  return `${years} лет`
}

function todosOf(profile: OwnCandidateDto): TodoItem[] {
  return [
    {
      id: 'test',
      label: 'Подтвердить грейд тестом',
      done: profile.assessmentStatus === 'passed',
      to: ROUTES.testing,
    },
    {
      id: 'fsp',
      label: 'Связать профиль с ФСП',
      done: profile.fspLinked,
      to: ROUTES.profileSettings,
    },
    {
      id: 'photo',
      label: 'Добавить фото',
      done: Boolean(profile.hasPhoto),
      to: ROUTES.profileResume,
    },
    {
      id: 'about',
      label: 'Рассказать о себе',
      done: Boolean(profile.about),
      to: ROUTES.profileResume,
    },
    {
      id: 'education',
      label: 'Указать образование',
      done: profile.education.length > 0,
      to: ROUTES.profileResume,
    },
    {
      id: 'github',
      label: 'Добавить ссылку на GitHub',
      done: Boolean(profile.githubUrl),
      to: ROUTES.profileResume,
    },
  ]
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
  const firstName = own.displayName.split(/\s+/)[0] || own.displayName
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
    <Page
      className="page--inset"
      title={`Здравствуйте, ${firstName}`}
      lead={
        fresh > 0
          ? `Новых приглашений: ${fresh}. Ответьте — работодатель ждёт.`
          : 'Новых приглашений нет. Заполненный профиль чаще попадает в подборку работодателей.'
      }
    >
      <div className="cabinet-grid">
        <div className="cabinet-col">
          <Panel
            title="Ждут вашего ответа"
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
                direction="incoming"
                emptyText="Сейчас ответа ничего не ждёт."
              />
            )}
          </Panel>
        </div>
        <div className="cabinet-col">
          <Panel
            title="Ваш профиль"
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
          <Panel title="Что сделать">
            <TodoList items={todosOf(own)} />
          </Panel>
        </div>
      </div>
    </Page>
  )
}
